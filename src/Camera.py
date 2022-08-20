#!/usr/bin/env python
import subprocess
from BaseClass import BaseRabbitMq,alive
import pika, sys, os
import cv2 as cv
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import uuid
import config
import time
import datetime

config.initConfig()
camera_script = config.getCell('camera')
hearbeat = config.getCell('hearbeat')
hearbeat_queue = config.getCell('queue_hearbeat')
queue_cam_to_detector = config.getCell('queue_cam_to_detector')

analizer_script = config.getCell('analizer')
path_logger = os.path.join('tmp')

LONG_TIME_STREAM = 1 * 60


class camera(BaseRabbitMq):
    def __init__(self,
                 id_cam,
                 id_header,
                 queue,
                 host):

        super().__init__(host)

        self.id_cam = id_cam
        self.id_header = id_header
        self.up_queue = queue
        self.host = host
        self.name_logger = f'{camera_script.split(".")[0]}_{id_cam}.txt'

        from main import db, Camera
        res = Camera.query.where(Camera.id == self.id_cam).all()
        self.name_cam = res[0].name_cam
        self.fps_video = res[0].fps_video
        # 1 если видеофайл
        self.video = res[0].all_frame

        self.cur_frame = None
        self.start_ts_unix = None
        self.all_frame = None
        self.url = None
        self.exit_error = False

        self.response = None
        self.process_analizer = None

        # Очередь для обмена сообщениями с Yolo
        self.execute_request(self.channel.queue_declare,queue=queue_cam_to_detector,
                                   durable=True)

        # Очередь для обмена сообщениями с Header
        self.execute_request(self.channel.queue_declare,queue=self.up_queue,
                                   durable=True)

        self.initial_queue()

    def connection_close(self):
        self.connection = None


    def up_events(self, ch, method, props, body):
        ask_js = json.loads(body)

        command, data = ask_js['command'], ask_js['data']
        messange = {}
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)
        close = False
        status = 2
        if command == 'delete':
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Сообщение на удаление камеры\n')
            self.delete_camera()
            return

        elif command == 'stop':
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Запрос на остановку камеры\n')
            self.update_camera()
            status = 0
            messange = {'command': 'info',
                        'data': {
                                'title': 'Сообщение системы',
                                'type': 'info',
                                 'info': f'Камера {self.name_cam} остановлена!'
                                    }}

            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Камера остановлена\n')
            close = True

        elif command == 'run':
            status = 2
            messange = {'command': 'info',
                        'data': {
                            'title': 'Сообщение системы',
                            'type': 'info',
                            'info': f'Камера {self.name_cam} запущена!'}}
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Камера запущена\n')

        elif command == 'editing':
            self.get_setting()
            messange = {'command': 'info',
                        'data': {
                            'title': 'Сообщение системы',
                            'type': 'info',
                            'info': f'Настройки камеры {self.name_cam} успешно обновлены!'}}
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Настройки камеры успешно обновлены\n')

        self.update_camera_process(status)

        self.execute_request(self.publish_messange,self.queue_out,
                              messange=messange)
        if close:
            self.connection_close()


    def low_events(self, ch, method, props, body):
        ask_js = json.loads(body)
        command, data = ask_js['command'], ask_js['data']
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

        if command == 'info':
            if data['type'] == 'info':
                self.execute_request(self.publish_messange,self.queue_out, {'command': 'info', 'data': data})


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


    def delete_camera(self):
        messange = {'command': 'info',
                    'data': {
                        'title': 'Сообщение системы',
                        'type': 'info',
                         'info': f'Камера {self.name_cam} удалена!'
                         }}

        self.execute_request(self.publish_messange,self.queue_out,messange=messange)

        from main import db, Camera, Camera_process
        res = Camera.query.where(Camera.id == self.id_cam).one()
        db.session.delete(res)

        res = Camera_process.query.where(Camera_process.cam_id == self.id_cam).one()
        self.execute_request(self.channel.queue_delete,res.queue_in)
        self.execute_request(self.channel.queue_delete,res.queue_out)
        self.execute_request(self.channel.queue_delete,res.queue_callback)
        self.execute_request(self.channel.queue_delete,res.queue_analizer_in)
        self.execute_request(self.channel.queue_delete,res.queue_analizer_out)

        db.session.delete(res)

        try:
            db.session.commit()
        except Exception as e:
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Ошибка {e}!\n')

            db.session.rollback()

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Камера удалена\n')
        self.connection_close()

    def initial_queue(self):
        from main import db, Camera_process, Camera
        res = Camera_process.query.where(Camera_process.cam_id == self.id_cam).first()
        if res == None:
            queue_in = str(uuid.uuid4())
            queue_out = str(uuid.uuid4())
            queue_callback = str(uuid.uuid4())

            queue_analizer_in = str(uuid.uuid4())
            queue_analizer_out = str(uuid.uuid4())

            new_cam = Camera_process(
                cam_id=self.id_cam,
                id_header=self.id_header,
                queue_in=queue_in,
                queue_out=queue_out,
                status=1,
                queue_callback=queue_callback,
                queue_analizer_out = queue_analizer_out,
                queue_analizer_in = queue_analizer_in,
            )

            try:
                db.session.add(new_cam)
                db.session.commit()
                print(f"Camera: Info load Header")
            except:
                res = Camera.query.where(Camera.id == self.id_cam).one()
                db.session.delete(res)
                messange = {'command': 'info',
                            'data': {
                                'title': 'Ошибка',
                                'type': 'danger',
                                 'info': f'Не удалось создать камеру - {self.name_cam}!'}}

                self.execute_request(self.publish_messange,self.queue_out,
                                      messange=messange)
                db.session.rollback()

                self.exit_error = True
                print(f"Camera: Error load info header")
                return

            res = {'queue_callback': queue_callback,
                   'queue_in': queue_in,
                   'queue_out': queue_out,
                   'queue_analizer_in': queue_analizer_in,
                   'queue_analizer_out': queue_analizer_out}
        else:
            res = {'queue_callback': res.queue_callback,
                   'queue_in': res.queue_in,
                   'queue_out': res.queue_out,
                   'queue_analizer_in': res.queue_analizer_in,
                   'queue_analizer_out': res.queue_analizer_out}

        self.execute_request(self.channel.queue_declare,queue=res['queue_in'],
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res['queue_out'],
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res['queue_callback'],
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res['queue_analizer_in'],
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res['queue_analizer_out'],
                                   durable=True)

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Инициализация камеры прошла успешно!\n')

        self.queue_analizer_out = res['queue_analizer_out']
        self.queue_analizer_in = res['queue_analizer_in']


        self.queue_in, self.queue_out, self.queue_callback = res['queue_in'], res['queue_out'], res['queue_callback']
        self.execute_request(self.channel.basic_consume,
            queue=res['queue_in'],
            on_message_callback=self.up_events
        )
        self.execute_request(self.channel.basic_consume,
            queue=res['queue_callback'],
            on_message_callback=self.detector_events
        )
        self.execute_request(self.channel.basic_consume,
            queue=res['queue_analizer_out'],
            on_message_callback=self.low_events
        )


    def detector_events(self, ch, method, props, body):
        self.response = True
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)


    def update_camera_process(self, status):
        from main import db, Camera_process
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Обновление статуса камеры\n')

        Camera_process.query.where(Camera_process.cam_id == self.id_cam).update({'status': status})
        try:
            db.session.commit()
        except Exception as e:
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Ошибка {e}!\n')
            db.session.rollback()


    def update_camera(self):
        from main import db, Camera
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Обновление обработанных кадров!\n')

        Camera.query.where(Camera.id == self.id_cam).update({"cur_frame": self.cur_frame + self.fps})
        try:
            db.session.commit()
        except Exception as e:
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Ошибка {e}!\n')
            db.session.rollback()


    def run(self):
        if not os.path.exists(os.path.join('tmp', self.id_cam)):
            os.makedirs(os.path.join('tmp', self.id_cam))

        global sched

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Камера запущена!\n')

        live = alive(self.host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[hearbeat_queue, {'type_proc': camera_script.split(".")[0],
                                                                          'id': f'{self.id_cam}',
                                                                          'name': self.name_cam
                                                                          }], seconds=hearbeat)
        sched.start()


        self.process_analizer = subprocess.Popen(["python",
                            f'./src/{analizer_script}',
                            str(self.id_cam),
                            self.queue_analizer_in,
                            self.queue_analizer_out,
                            f'{self.id_header}',
                            host])

        if self.exit_error:
            return


        messange = {'command': 'info',
                    'data': {'title':"Сообщение системы",
                             'type': 'ask',
                             'id': self.id_cam,
                             'queue_in': self.queue_in,
                             'queue_out': self.queue_out,
                             'info': f'Камера: {self.name_cam} успешно создана!'
                             }}

        self.execute_request(self.publish_messange,self.up_queue,messange)
        self.execute_request(self.publish_messange,hearbeat_queue,{'type_proc': camera_script.split(".")[0],
                                                  'id': f'{self.id_cam}',
                                                  'name': self.name_cam
                                                  })

        self.get_setting()
        self.update_camera_process(2)

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Началась обработка видео!\n')

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Началась обработка видео!\n')

        cap = cv.VideoCapture(self.url)
        if cap.isOpened() == None:
            sched.shutdown()
            return

        cap.set(cv.CAP_PROP_POS_FRAMES, self.cur_frame)

        delete_frame_id = LONG_TIME_STREAM*self.fps_video + 200

        cur_frame = self.cur_frame
        count_error = 0
        count_frame_save_bd = 0
        while not self.connection is None:
            ret, frame = cap.read()
            if ret == True:
                if cur_frame % 100 == 0:
                    cv.imwrite(f'./src/static/img/cam_{self.id_cam}.jpg',frame)

                if cur_frame % self.fps == 0:
                    # Сохранение прогресса камеры
                    if count_frame_save_bd % 5==0:
                        self.update_camera()
                        count_frame_save_bd = 0

                    frame = cv.resize(frame, (640, 640))

                    # Сохранение фрейма для видео
                    cv.imwrite(os.path.join('tmp',self.id_cam,f'{cur_frame}.jpg'), frame)
                    cur_name = f'{int(cur_frame - delete_frame_id)}.jpg'
                    print(f'id {self.id_cam} cur_del {cur_name}')
                    if self.video != 1 and os.path.exists(os.path.join('tmp', self.id_cam, f'{int(cur_frame - delete_frame_id)}.jpg')):
                        os.remove(os.path.join('tmp', self.id_cam, f'{int(cur_frame - delete_frame_id)}.jpg'))

                    cur_ts = self.start_ts_unix + (cur_frame // self.fps_video)

                    message = {'cam_id':self.id_cam,
                               'ts': cur_ts,
                                'frame_id': cur_frame,
                               'count_frame': cur_frame/self.fps,
                               'queue_analizer':self.queue_analizer_in,
                               'frame': frame.tolist()}

                    print(f'Camera: Кадр {cur_frame} отправлен')
                    self.execute_request(self.channel.basic_publish,exchange='',
                                               routing_key=queue_cam_to_detector,
                                               properties=pika.BasicProperties(
                                                   reply_to=self.queue_callback),
                                               body=json.dumps(message))

                    self.cur_frame = cur_frame
                    while self.response is None and not self.connection is None:
                        self.execute_request(self.connection.process_data_events)

                    self.response = None
                    count_frame_save_bd +=1
                cur_frame += 1

            else:
                count_error +=1
                if count_error>100:
                    if self.all_frame==0:
                        cap = cv.VideoCapture(self.url)
                        cap.set(cv.CAP_PROP_POS_FRAMES, self.cur_frame)
                        continue
                    break

        cap.release()
        if count_error > 100:
            if self.all_frame == 1:
                self.update_camera_process(-1)
            else:
                self.update_camera_process(0)

        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Камера завершила работу!\n')
        sched.shutdown()


    # Получить последний фрейь для обработки
    def get_setting(self):
        from main import db, Camera
        res = Camera.query.where(Camera.id == self.id_cam).first()
        self.cur_frame = max(0, res.cur_frame - 1)
        self.fps = res.fps

        if res.start_ts == None:
            self.start_ts_unix = int(time.mktime(datetime.datetime.now().timetuple()))
        else:
            self.start_ts_unix = int(time.mktime(res.start_ts.timetuple()))

        self.all_frame = res.all_frame
        self.url = res.url


if __name__ == "__main__":
    try:
        id_cam = ''.join(sys.argv[1])
        queue = ''.join(sys.argv[2])
        id_header = ''.join(sys.argv[3])
        host = ''.join(sys.argv[4])

        cam = camera(id_cam, id_header, queue, host)
        cam.run()


    except KeyboardInterrupt:
        print('Camera: Interrupted')
        sched.shutdown()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
