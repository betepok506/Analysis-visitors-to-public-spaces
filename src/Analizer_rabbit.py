#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
from apscheduler.schedulers.background import BackgroundScheduler
from scipy.spatial import distance
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon as Pol
import time
import uuid
import numpy as np
import config
from BaseClass import BaseRabbitMq,alive
import time
import datetime
import KalmanFilter



config.initConfig()
host = config.getCell('host')
hearbeat = config.getCell('hearbeat')
hearbeat_queue = config.getCell('queue_hearbeat')
analizer_script = config.getCell('analizer')
# stream_queue = config.getCell('stream_queue')

# queue_in_analizer = 'queue_in_analizer'
# queue_out_analizer = 'queue_out_analizer'
path_logger = os.path.join('tmp')


class Analizer(BaseRabbitMq):
    def __init__(self,
                 id_analizer,  # Id анализер == id_камеры
                 queue_in,  # Название очереди для связи с вышестоящим элементом
                 queue_out,
                 id_header,  # Id хедера
                 host):  # Адрес сервера RabbitMQ

        super().__init__(host)

        self.name_logger = f"{analizer_script.split('.')[0]}_{id_analizer}.txt"
        self.id_analizer = int(id_analizer)
        self.id_header = id_header
        self.queue_out = queue_out
        self.queue_in = queue_in
        self.host = host

        self.kf = KalmanFilter.KalmanFilter()
        self.track = dict()
        self.track[1e9] = {'x': 1e9,
                          'y': 1e9,
                          'last_frame': 0}


        # Загрузка информации о камере
        self.camera = self.load_camera()
        self.cnt_predict = 15
        from main import db, Polygon
        self.camera_polygons = Polygon.query.all()
        self.min_square_bbox = self.camera.min_square_bbox
        self.cnt_to_del = self.camera.cnt_fps_del
        self.max_dist = self.camera.max_dist_between_bbox
        # Очередь для обмена сообщениями с Camera

        self.execute_request(self.channel.queue_declare,queue=self.queue_out,
                                   durable=True)


        self.execute_request(self.channel.queue_declare,queue=self.queue_in,
                                   durable=True)

        self.execute_request(self.channel.basic_consume,queue=self.queue_in,
                                    on_message_callback=self.up_event)

    def up_event(self, ch, method, props, body):
        from main import db
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)
        ask_js = json.loads(body)
        self.count_frame, data = ask_js['count_frame'], ask_js['data']
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Обрабатываю фрейм: {self.count_frame} \n')

        points, all_dist = self.get_all_dist(data, self.count_frame)
        all_dist.sort(key=lambda x: x[0])

        used = set()

        if 1e9 in self.track:
            self.track.pop(1e9)

        cnt_obn = 0
        for cur_dist in all_dist:
            if (cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y']) in used or \
                    (cur_dist[1]['track_x'], cur_dist[1]['track_y']) in used:
                continue

            if cur_dist[0] > self.max_dist:
                break

            cnt_obn += 1

            used.add((cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y']))
            used.add((cur_dist[1]['track_x'], cur_dist[1]['track_y']))

            points.remove((cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y'],
                           (cur_dist[1]['bbox_r'] - cur_dist[1]['bbox_l']) / (
                                   cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t']),
                           cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t'],
                           cur_dist[1]['id_bboxes']))

            update_mean, update_covariance = self.kf.update(self.track[cur_dist[1]['id_person']]['mean'],
                                                       self.track[cur_dist[1]['id_person']]['covariance'],
                                                       np.array([cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y'],
                                                                 (cur_dist[1]['bbox_r'] - cur_dist[1]['bbox_l']) / (
                                                                         cur_dist[1]['bbox_b'] - cur_dist[1][
                                                                     'bbox_t']),
                                                                 (cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t'])]))

            # self.draw( frame,cur_dist,self.track[cur_dist[1]['id_person']]['person_id'],15)

            area_id = self.which_area(cur_dist[1]['bbox_x'],
                                 cur_dist[1]['bbox_y'])

            self.insert_people_map(cur_dist[1]['id_person'],
                              cur_dist[1]['id_bboxes'],
                              area_id)

            # # Предсказание нового местарасположения

            # # Обновление информации
            self.track[cur_dist[1]['id_person']]['mean'] = update_mean
            self.track[cur_dist[1]['id_person']]['covariance'] = update_covariance
            self.track[cur_dist[1]['id_person']]['x'] = int(update_mean[0])
            self.track[cur_dist[1]['id_person']]['y'] = int(update_mean[1])
            self.track[cur_dist[1]['id_person']]['last_frame'] += 1

        print(f'Количество обнаруженных старых {cnt_obn}')
        cnt_new = 0
        for cur_points in points:
            cnt_new += 1
            mean, covariance = self.kf.initiate(
                np.array([cur_points[0], cur_points[1],
                          cur_points[2],
                          cur_points[3]]))

            man_id = self.insert_people()
            self.track[man_id] = {'x': int(mean[0]),
                             'y': int(mean[1]),
                             'person_id': man_id,
                             'mean': mean,
                             'covariance': covariance,
                             'last_frame': self.count_frame}

            area_id = self.which_area(cur_points[0],
                                 cur_points[1])

            self.insert_people_map(man_id,
                              cur_points[-1],
                              area_id)

        print(f'Количество новых {cnt_new}')
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Кличество новых: {cnt_obn}, Количество старых: {cnt_new}\n')

        self.prediction_further_path(self.count_frame)

        if self.count_frame > 0 and self.count_frame % 3 == 0:
            print(f"{self.cur_time()} processed {self.count_frame} frame for camera #{self.id_analizer}")
            try:
                db.session.commit()
            except:
                db.session.rollback()


        self.count_frame += 1

        db.session.commit()
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Обработка кадра прошла успешно!\n')


    def execute_request(self,func, *args, **kwargs):
        cnt = 0
        while cnt < 5:
            try:
                func(*args, **kwargs)
                break
            except Exception as e:
                parameters = pika.URLParameters(f'amqp://guest:guest@{self.host}/')
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.start_consuming()
                cnt+=1
                if cnt==5:
                    raise e


    def draw(self, frame,  cur_dist, cur_person, cnt):
        cv.rectangle(frame, (cur_dist[1]['bbox_l'], cur_dist[1]['bbox_t']),
                     (cur_dist[1]['bbox_r'], cur_dist[1]['bbox_b']),
                     ((255 + cnt * cur_person) % 256,
                      (255 + 2 * cnt * cur_person) % 256,
                      (255 + 7 * cnt * cur_person) % 256),
                     thickness=2)

        cv.arrowedLine(frame, (self.track[cur_dist[1]['id_person']]['x'] + 10,
                               self.track[cur_dist[1]['id_person']]['y'] + int(
                                   self.track[cur_dist[1]['id_person']]['mean'][3]) // 2 + 10),
                       (int(self.track[cur_dist[1]['id_person']]['mean'][0]) + 10,
                        int(self.track[cur_dist[1]['id_person']]['mean'][1]) + int(
                            self.track[cur_dist[1]['id_person']]['mean'][3]) // 2 + 10),
                       color=((255 + cnt * cur_person) % 256,
                              (255 + 2 * cnt * cur_person) % 256,
                              (255 + 7 * cnt * cur_person) % 256)
                       )
        cv.putText(img=frame,
                   text=str(cur_person),
                   org=(cur_dist[1]['bbox_l'], cur_dist[1]['bbox_t'] + 50),
                   fontFace=cv.FONT_HERSHEY_PLAIN,
                   fontScale=2,
                   color=((255 + cnt * cur_person) % 256,
                          (255 + 2 * cnt * cur_person) % 256,
                          (255 + 7 * cnt * cur_person) % 256),
                   thickness=2)


    def cur_time(self):
        return datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")


    def prediction_further_path(self, count_frame):
        for id_person in self.track.keys():
            if self.track[id_person]['last_frame'] - count_frame < self.cnt_predict:
                upgrade_mean, upgrade_covariance = self.kf.update(self.track[id_person]['mean'],
                                                             self.track[id_person]['covariance'],
                                                             np.array([self.track[id_person]['x'], self.track[id_person]['y'],
                                                                       self.track[id_person]['mean'][2],
                                                                       self.track[id_person]['mean'][3]]))
                self.track[id_person]['mean'], self.track[id_person][
                    'covariance'] = self.kf.predict(upgrade_mean, upgrade_covariance)
                self.track[id_person]['x'] = int(self.track[id_person]['mean'][0])
                self.track[id_person]['y'] = int(self.track[id_person]['mean'][1])


    def which_area(self, row, col):
        for cur_camera in self.camera_polygons:
            if cur_camera.cam_id != self.id_analizer:
                continue

            # x, y = (cur_bbox.r + cur_bbox.l) / 2, (cur_bbox.b + cur_bbox.t) / 2
            if self.is_polygon(col, row, cur_camera.polygon):
                return cur_camera.area_id
        return 1e5 + self.id_analizer


    def is_polygon(self, x, y, points):
        zone = Pol(points)
        return zone.contains(Point((x, y)))


    def insert_people(self):
        from main import db, People
        new_people = People(clss=0,
                            cam_id=self.id_analizer)
        try:
            db.session.add(new_people)
            # db.session.commit()
            print(f"New people {new_people.id} loaded")
        except:
            db.session.rollback()
            print(f"New people {new_people.id} already exists")

        res = People.query.filter_by(clss=0, cam_id=self.id_analizer).order_by(People.id.desc()).first().id
        return res


    def insert_people_map(self, man_id, bboxes_id, area_id):
        from main import db, PeopleMap
        new_people_map = PeopleMap(area_id=area_id,
                                   bbox_id=bboxes_id,
                                   person_id=man_id)
        # print('new_people_map',new_people_map)
        try:
            db.session.add(new_people_map)
            db.session.commit()
            print(f"People_map {man_id} loaded")
        except:
            db.session.rollback()
            print(f"People_map {man_id} already exists")

        return


    # Загрузка информации о камере
    def load_camera(self):
        from main import db, Camera
        res = Camera.query.filter_by(id=self.id_analizer).order_by(Camera.id).first()
        return res


    def get_all_dist(self, res, count_frame):

        all_dist = []  # Массив дистанций от каждой точки до каждой
        points = set()  # Множество точек центров Bboxes
        for bbox in res:
            if (bbox['r'] - bbox['l']) * (bbox['b'] - bbox['t']) < self.min_square_bbox:
                continue

            bbox_x = bbox['l'] + (bbox['r'] - bbox['l']) // 2
            bbox_y = bbox['t'] + (bbox['b'] - bbox['t']) // 2
            points.add((bbox_x, bbox_y,
                        (bbox['r'] - bbox['l']) / (bbox['b'] - bbox['t']),
                        (bbox['b'] - bbox['t']),
                        bbox['id']))

            id_person_del = []

            for id_person in self.track.keys():
                if count_frame - self.track[id_person]['last_frame'] > self.cnt_to_del:
                    id_person_del.append(id_person)
                    continue

                dist = distance.euclidean((bbox_x, bbox_y), (self.track[id_person]['x'], self.track[id_person]['y']))
                all_dist.append([dist, {'bbox_x': bbox_x, 'bbox_y': bbox_y,
                                        'track_x': self.track[id_person]['x'], 'track_y': self.track[id_person]['y'],
                                        'bbox_l': bbox['l'], 'bbox_r': bbox['r'],
                                        'bbox_b': bbox['b'], 'bbox_t': bbox['t'],
                                        'id_person': id_person,
                                        'id_bboxes': bbox['id']}])

            # Удаление всех точек которые давно не использовались
            for id_person in id_person_del:
                self.track.pop(id_person)

        return points, all_dist


    def run(self):
        global sched
        # print(f'Anflizer camera: {self.id_analizer} run!')
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Анализер запущен!\n')
        messange = {'command': 'info',
                    'data': {
                        'title': 'Сообщение системы',
                        'type': 'info',
                         'id': self.id_analizer,
                         'info': f'Анализер: {self.id_analizer} успешно создан!'
                         }}

        self.execute_request(self.publish_messange,self.queue_out, messange)

        live = alive(self.host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[hearbeat_queue, {'type_proc': analizer_script.split(".")[0],
                                                                          'id': f'{self.id_analizer}',
                                                                          }], seconds=hearbeat)
        sched.start()

        while not self.channel is None:
            try:
                self.execute_request(self.channel.start_consuming)
            except:
                parameters = pika.URLParameters(f'amqp://guest:guest@{self.host}/')
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.start_consuming()

        sched.shutdown()

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Анализер завершил свою работу!\n')



if __name__ == "__main__":
    try:
        id_analizer = ''.join(sys.argv[1])
        queue_analizer_in = ''.join(sys.argv[2])
        queue_analizer_out = ''.join(sys.argv[3])
        header_id = ''.join(sys.argv[4])
        host = ''.join(sys.argv[5])

        n = Analizer(id_analizer,
                     queue_analizer_in,
                     queue_analizer_out,
                     header_id,
                     host)
        n.run()

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except KeyboardInterrupt:
        print('Analizer: Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)