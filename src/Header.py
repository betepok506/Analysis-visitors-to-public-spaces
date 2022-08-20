#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
import numpy as np
from BaseClass import BaseRabbitMq, alive
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
import subprocess
import uuid
import config

config.initConfig()

hearbeat = config.getCell('hearbeat')
queue_hearbeat = config.getCell('queue_hearbeat')
host = config.getCell('host')

classifaer_script = config.getCell('classifaer')
detector_script = config.getCell('detector')
web_script = config.getCell('web')
heartbeat_script = config.getCell('heartbeat')
header_script = config.getCell('header')
camera_script = config.getCell('camera')

path_logger = os.path.join('tmp')


class Header(BaseRabbitMq):
    def __init__(self,
                 name_header,  # Имя хедера используемое пользователем
                 up_queue,  # Очередь, используемая для связи с WEB
                 host):  # Адрес сервера RabbitMQ
        super().__init__(host)

        self.name_logger = f'{header_script.split(".")[0]}_{1}.txt'
        self.host = host
        self.up_queue = up_queue
        self.name_header = name_header

        self.run_process = {}
        # Очередь WEB
        self.execute_request(self.channel.queue_declare,queue=self.up_queue,
                                   durable=True)

        self.hearbeat_queue = queue_hearbeat
        self.execute_request(self.channel.queue_declare,queue=self.hearbeat_queue,
                                   durable=True)

        self.initial_queue()

    def initial_queue(self):
        from main import db, Header_process
        res = Header_process.query.filter_by(name_header=self.name_header).first()
        ok = True
        if res == None:
            queue_header = str(uuid.uuid4())
            queue_in = str(uuid.uuid4())
            queue_out = str(uuid.uuid4())

            new_header = Header_process(
                name_header=self.name_header,
                queue_in=queue_in,
                queue_out=queue_out,
                status=1,
                queue_header=queue_header
            )

            try:
                db.session.add(new_header)
                db.session.commit()
                # self.write_logger(path_logger, self.name_logger,
                #                   f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                #                   f'Информация о хедере загружена в бд!\n')
                print(f"Header: Info load Header")
            except:
                db.session.rollback()
                ok = False
                # self.write_logger(path_logger, self.name_logger,
                #                   f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                #                   f'Ошибка загрузки информации в бд!\n')
                print(f"Header: Error load info header")

            res = Header_process.query.where(Header_process.name_header == self.name_header).first()

        res = {'id': res.id,
               'queue_consume': res.queue_header,
               'queue_in': res.queue_in,
               'queue_out': res.queue_out}

        self.queue_in, self.queue_out, self.queue_consume = res['queue_in'], res['queue_out'], res['queue_consume']
        self.header_id = res['id']
        self.name_logger = f'{header_script.split(".")[0]}_{self.header_id}.txt'
        self.execute_request(self.channel.queue_declare,queue=res['queue_in'],
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res['queue_out'],
                                   durable=True)

        # Очередь для общения с дочерними приложениями
        self.execute_request(self.channel.queue_declare,queue=res['queue_consume'],
                                   durable=True)

        # Сообщения от дочерних узлов
        self.execute_request(self.channel.basic_consume,
            queue=res['queue_consume'],
            on_message_callback=self.low_events
        )
        # Сообщения от Web
        self.execute_request(self.channel.basic_consume,
            queue=res['queue_in'],
            on_message_callback=self.up_events
        )

    # Получть очередь для данного типа объекта с заданным id
    def get_queue(self, type, id_):
        if type == camera_script.split('.')[0]:
            from main import db, Camera_process
            res = Camera_process.query.where(Camera_process.cam_id == id_).first()
            return res.queue_in

        elif type == classifaer_script.split('.')[0]:
            from main import db, Classifaer_process
            res = Classifaer_process.query.where(Classifaer_process.id == id_).first()
            return res.queue_in
        elif type == detector_script.split('.')[0]:
            from main import db, Detector_process
            res = Detector_process.query.where(Detector_process.id == id_).first()
            return res.queue_in

    # Получение событий от WEB
    def up_events(self, ch, method, props, body):

        ask_js = json.loads(body)
        command, data = ask_js['command'], ask_js['data']
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

        name_proc = f'{data["type"]}_{data["id"]}'
        if command == "create" or command == 'run':
            if name_proc in self.run_process:
                ret_cod = self.run_process[name_proc].poll()
                if ret_cod == None:
                    return

            self.run_process[name_proc] = subprocess.Popen(["python",
                                                            f'./src/{data["type"]}',  # camera.py
                                                            str(data["id"]),  # id process
                                                            self.queue_consume,  # очередь
                                                            f'{self.header_id}',
                                                            data['host'],
                                                            ])
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Процесс {name_proc} создан!\n')



        elif command == 'delete' and data['type'] == header_script.split('.')[0]:
            from main import db, Header_process, Camera_process, Classifaer_process, Detector_process
            self.execute_request(self.publish_messange,self.queue_out, {'command': 'info',
                                                   'data': {
                                                       'title': 'Сообщение системы',
                                                       'type': 'info',
                                                       'info': 'Завершение дочерних процессов хедера'
                                                   }})
            self.deleting_child_processes()
            self.execute_request(self.channel.stop_consuming)

        else:
            queue = self.get_queue(data['type'], data['id'])

            self.execute_request(self.publish_messange,queue, {'command': f'{command}',
                                          'data': {'type': data['type'],
                                                   'id': data['id']}})

    def deleting_child_processes(self):
        from main import db, Header_process, Camera_process, Classifaer_process, Detector_process

        res = Header_process.query.where(Header_process.id == self.header_id).first()

        child_process = Camera_process.query.where(Camera_process.id_header == self.header_id).all()
        for camera in child_process:
            messange = {'command': 'delete',
                        'data': {'type': camera_script.split('.')[0],
                                 'id': camera.id,
                                 'host': host}}
            self.execute_request(self.publish_messange,camera.queue_in, messange)

        child_process = Classifaer_process.query.where(Classifaer_process.id_header == self.header_id).all()
        for classifaer in child_process:
            messange = {'command': 'delete',
                        'data': {'type': classifaer_script.split('.')[0],
                                 'id': classifaer.id,
                                 'host': host}}
            self.execute_request(self.publish_messange,classifaer.queue_in, messange)

        child_process = Detector_process.query.where(Detector_process.id_header == self.header_id).all()
        for detector in child_process:
            messange = {'command': 'delete',
                        'data': {'type': detector_script.split('.')[0],
                                 'id': detector.id,
                                 'host': host}}
            self.execute_request(self.publish_messange,detector.queue_in, messange)

        self.execute_request(self.channel.queue_delete,self.queue_in)
        self.execute_request(self.channel.queue_delete,self.queue_out)
        self.execute_request(self.channel.queue_delete,self.queue_consume)
        db.session.delete(res)
        try:
            db.session.commit()
        except Exception as e:
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Ошибка {e}!\n')

            db.session.rollback()

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

    def low_events(self, ch, method, props, body):
        try:
            ask_js = json.loads(body)

            command, data = ask_js['command'], ask_js['data']

            self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

            if command == 'info':
                if data['type'] == 'ask':
                    self.execute_request(self.channel.queue_declare,queue=data['queue_in'],
                                               durable=True)
                    self.execute_request(self.channel.queue_declare,queue=data['queue_out'],
                                               durable=True)

                    self.execute_request(self.channel.basic_consume,
                        queue=data['queue_out'],
                        on_message_callback=self.low_events
                    )

                    self.execute_request(self.channel.basic_publish,exchange='',
                                               routing_key=self.queue_out,
                                               body=json.dumps({'command': 'info',
                                                                'data': {
                                                                    'title': 'Успешно!',
                                                                    'type': 'success',
                                                                    'info': data['info']
                                                                }}))
                elif data['type'] == 'info':
                    # print(f'Header: Событие info {data}')
                    self.execute_request(self.publish_messange,self.queue_out, {'command': 'info', 'data': data})

            else:
                # print(f'Header: Событие {command}')
                self.execute_request(self.publish_messange,self.queue_out,
                                      {'command': command, 'data': data})

        except:
            self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

    def run(self):
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Хедер запустился!\n')

        # Подтверждение создания
        self.execute_request(self.publish_messange,self.up_queue, {'command': 'info',
                                              'data': {
                                                  'title': 'Сообщение системы',
                                                  'type': 'ask',
                                                  'id': self.queue_consume,
                                                  'name': self.name_header,
                                                  'queue_in': self.queue_in,
                                                  'queue_out': self.queue_out,
                                                  'info': f'Header {self.name_header} запущен!'
                                              }})

        self.execute_request(self.publish_messange,queue_hearbeat, {'type_proc': header_script.split(".")[0],
                                               'id': f'{self.header_id}',
                                               'name': self.name_header
                                               })

        live = alive(host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[queue_hearbeat, {'type_proc': header_script.split(".")[0],
                                                                          'id': f'{self.header_id}',
                                                                          # 'id_header': 0,
                                                                          'name': self.name_header
                                                                          }], seconds=hearbeat)
        sched.start()

        while not self.channel is None:
            try:
                self.channel.start_consuming()
            except:
                parameters = pika.URLParameters(f'amqp://guest:guest@{self.host}/')
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.start_consuming()

        # print('Прослушивание остановлено!')
        sched.shutdown()
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Хедер завершил работу!\n')


if __name__ == "__main__":

    try:
        name_header = ''.join(sys.argv[1])
        name_queue = ''.join(sys.argv[2])
        host = ''.join(sys.argv[3])
        n = Header(name_header, name_queue, host)
        n.run()
    except KeyboardInterrupt:
        print('Header: Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
