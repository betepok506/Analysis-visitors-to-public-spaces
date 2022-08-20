#!/usr/bin/env python
import datetime
import random
from BaseClass import BaseRabbitMq,alive
import pika, sys, os
import cv2 as cv
import json
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import config

config.initConfig()

hearbeat = config.getCell('hearbeat')
queue_hearbeat = config.getCell('queue_hearbeat')
queue_cam_to_detector = config.getCell('queue_cam_to_detector')
host = config.getCell('host')
detector_script = config.getCell('detector')

queue_classifaer_age = config.getCell('queue_classifaer_age')
queue_classifaer_gender = config.getCell('queue_classifaer_gender')

from yolov5.yolo_detector import YoloDetector

os.environ["CUDA_VISIBLE_DEVICES"]="0"
detector = None
path_logger = os.path.join('tmp')

class Detector(BaseRabbitMq):
    def __init__(self,
                 id_detector,
                 id_header,
                 queue,
                 host):

        super().__init__(host)

        self.name_logger = f"{detector_script.split('.')[0]}_{id_detector}.txt"
        self.path_logger = path_logger

        self.id_detector = id_detector
        self.up_queue = queue
        self.id_header = id_header
        self.host = host
        self.cnt_check_classif = 0
        self.hearbeat_queue = queue_hearbeat

        self.execute_request(self.channel.queue_declare,queue=queue_classifaer_age,
                                   durable=True)

        self.execute_request(self.channel.queue_declare,queue=queue_classifaer_gender,
                                   durable=True)

        self.execute_request(self.channel.queue_declare,queue=queue_cam_to_detector,
                                   durable=True)

        self.execute_request(self.channel.basic_consume,queue=queue_cam_to_detector,
                                   on_message_callback=self.on_request)
        self.initial_queue()


    def initial_queue(self):
        from main import db, Detector_process

        res = Detector_process.query.where(Detector_process.id == self.id_detector).first()
        self.execute_request(self.channel.queue_declare,queue=res.queue_in,
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res.queue_out,
                                   durable=True)

        self.queue_in, self.queue_out = res.queue_in, res.queue_out
        self.id_detector = res.id
        self.execute_request(self.channel.basic_consume,
            queue=res.queue_in,
            on_message_callback=self.up_events
        )
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Инициализация параметров прошла успешно!\n')

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


    def on_request(self, ch, method, props, body):
        save_to_db = True
        js = json.loads(body)
        frame = np.array(js['frame'], dtype=np.uint8)
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Кадр получен!\n')

        cv.imwrite(f"tmp/{self.id_detector}_last.png", frame)
        cur_img_res = self.yolo_predict(f"tmp/{self.id_detector}_last.png")

        # Проверка запущенных классификаторов, если их нет не кидать фреймы
        if self.cnt_check_classif % 10 == 0:
            from main import db, Classifaer_process
            res = Classifaer_process.query.all()
            if len(res) == 0:
                # Поставить return тогда подтверждения не будет и обработки тоже!!!
                self.classifaer = False
            else:
                self.classifaer = True

        bbox = []
        for cur_bbox in cur_img_res:

            left = cur_bbox["left"]
            right = cur_bbox["right"]
            top = cur_bbox["top"]
            bottom = cur_bbox["bottom"]
            tp = cur_bbox["class"]

            from main import db, BBoxes
            try:
                bbox_id = BBoxes.query.order_by(BBoxes.id.desc()).first().id
            except:
                bbox_id = 0
                
            bbox_id += 1

            new_bbox = BBoxes(
                cam_id=js['cam_id'],
                l=left,
                r=right,
                t=top,
                b=bottom,
                ts=datetime.datetime.fromtimestamp(js['ts']),
                tp=tp,
                gender=-1,
                age=-1,
                frame_id=js['frame_id'])
            if tp == 0:
                bbox.append(
                    {'l':left,
                    'r':right,
                    't':top,
                    'b':bottom,
                    'id':bbox_id})

            # cv.rectangle(frame, (left, top), (right, bottom),
            #              (0,255,0),thickness=2)

            if save_to_db:
                try:
                    db.session.add(new_bbox)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing frame {js['frame_id'],} of {js['cam_id']}")
                    print(e)

            if self.classifaer == True:
                self.execute_request(self.publish_messange,queue_classifaer_gender,
                                      {'bbox_id':bbox_id,
                                       'frame':frame[top:top+(bottom-top),left: left + (right - left)].tolist()})

                self.execute_request(self.publish_messange,queue_classifaer_age,
                                      {'bbox_id': bbox_id,
                                       'frame': frame[top:top + (bottom - top), left: left + (right - left)].tolist()})
            bbox_id += 1

        # cv.imshow('Detector', frame)
        # cv.waitKey()
        # cv.destroyAllWindows()

        self.cnt_check_classif += 1

        self.execute_request(self.channel.queue_declare,queue=js['queue_analizer'],
                                   durable=True)

        self.execute_request(self.publish_messange,js['queue_analizer'],
                              {'data': bbox,
                               'count_frame': js['count_frame']})

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Кадр обработан и отправлен!\n')

        try:
            self.execute_request(ch.basic_publish,exchange='', routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id=props.correlation_id),
                             body=f"{js['frame_id']}")
        except Exception as e:
            print(f'Detector: {e}')

        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)


    def up_events(self, ch, method, props, body):
        ask_js = json.loads(body)
        command, data = ask_js['command'], ask_js['data']
        messange = {}
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)
        close = False
        if command == 'delete':
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Запрос на удаление детектора\n')

            messange = {'command': 'info',
                        'data': {
                            'title': 'Сообщение системы',
                            'type': 'info',
                             'info': f'Детектор {self.id_detector} удален!'}}

            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Детектор удален\n')
            close = True

        self.execute_request(self.publish_messange,self.queue_out,messange=messange)

        if close:
            from main import db, Detector_process
            res = Detector_process.query.where(Detector_process.id == self.id_detector).first()
            self.execute_request(self.channel.queue_delete,self.queue_in)
            self.execute_request(self.channel.queue_delete,self.queue_out)

            db.session.delete(res)

            try:
                db.session.commit()
            except Exception as e:
                print(f'Detector: {e}')
                db.session.rollback()

            self.execute_request(self.channel.stop_consuming)
            self.channel = None


    def connection_close(self):
        self.execute_request(self.connection.close)
        self.connection = None


    def yolo_predict(self, filename):
        global detector
        if detector is None:
            detector = YoloDetector()
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Загрузка модели прошла успешно!\n')

        return detector.predict(filename)


    def run(self):
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Детектор запустился\n')

        self.execute_request(self.publish_messange,self.up_queue, {'command': 'info',
                                              'data': {'type': 'ask',
                                                       'title': 'Сообщение системы',
                                                       'id': self.id_detector,
                                                       'queue_in': self.queue_in,
                                                       'queue_out': self.queue_out,
                                                       'info': f'Детектор № {self.id_detector} запущен!'
                                                       }})

        self.execute_request(self.publish_messange,queue_hearbeat, {'type_proc': detector_script.split('.')[0],
                                                    'id': f'{self.id_detector}'})

        live = alive(host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[queue_hearbeat, {'type_proc': detector_script.split('.')[0],
                                                                          'id': f'{self.id_detector}',
                                                                          }], seconds=hearbeat)
        sched.start()
        global detector
        if detector is None:
            detector = YoloDetector()


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
                          f'Детектор остановлен!\n')


if __name__ == "__main__":
    try:
        id_detector = ''.join(sys.argv[1])
        queue = ''.join(sys.argv[2])
        id_header = ''.join(sys.argv[3])
        host = ''.join(sys.argv[4])

        n = Detector(id_detector,id_header, queue, host)
        n.run()
    except KeyboardInterrupt:
        print('Detector: Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
