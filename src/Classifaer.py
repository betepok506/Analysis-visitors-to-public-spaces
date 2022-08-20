#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
import numpy as np
import time
import datetime
from BaseClass import BaseRabbitMq,alive
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import config
from Classif_model import vgg16_classifaer
config.initConfig()

hearbeat = config.getCell('hearbeat')
queue_hearbeat = config.getCell('queue_hearbeat')
queue_cam_to_detector = config.getCell('queue_cam_to_detector')
host = config.getCell('host')
detector_script = config.getCell('detector')
classifaer_script = config.getCell('classifaer')

queue_classifaer_age = config.getCell('queue_classifaer_age')
queue_classifaer_gender = config.getCell('queue_classifaer_gender')


path_logger = os.path.join('tmp')
class Classifaer(BaseRabbitMq):
    def __init__(self,
                 id_classifaer,
                 id_header,
                 queue,
                 host):

        super().__init__(host)

        self.type_classifaer = None
        self.id_classifaer = id_classifaer
        self.up_queue = queue
        self.id_header = id_header
        self.host = host
        self.path_logger = path_logger
        self.name_logger = f"{classifaer_script.split('.')[0]}_{id_classifaer}.txt"

        self.exit = False
        self.hearbeat_queue = queue_hearbeat

        self.initial_queue()

    def initial_queue(self):
        from main import db, Classifaer_process

        res = Classifaer_process.query.where(Classifaer_process.id == self.id_classifaer).first()
        self.execute_request(self.channel.queue_declare,queue=res.queue_in,
                                   durable=True)
        self.execute_request(self.channel.queue_declare,queue=res.queue_out,
                                   durable=True)

        self.queue_in, self.queue_out = res.queue_in, res.queue_out
        self.id_classifaer = res.id
        self.execute_request(self.channel.basic_consume,
            queue=res.queue_in,
            on_message_callback=self.up_events
        )

        if res.type_classifaer == 1:
            self.type_classifaer = 'age'
            self.execute_request(self.channel.queue_declare,queue=queue_classifaer_age,
                                       durable=True)

            self.execute_request(self.channel.basic_consume,queue=queue_classifaer_age,
                                       on_message_callback=self.on_request)
        else:
            self.type_classifaer = 'gender'
            self.execute_request(self.channel.queue_declare,queue=queue_classifaer_gender,
                                       durable=True)

            self.execute_request(self.channel.basic_consume,queue=queue_classifaer_gender,
                                       on_message_callback=self.on_request)

        self.load_model()
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Инициализация классификатора прошла успешно!\n')

    def on_request(self, ch, method, props, body):
        js = json.loads(body)
        bbox_id, frame = js['bbox_id'], np.array(js['frame'], dtype=np.uint8)

        cv.imwrite(f"tmp/_classifaer{self.id_classifaer}_last.png", frame)
        top_probabilities,res_class = self.model.predict(f"tmp/_classifaer{self.id_classifaer}_last.png", 1)
        from main import BBoxes, db
        if self.type_classifaer == 'age':
            classes = ['personalLess15','personalLess30','personalLarger60']
            res_class = classes.index(res_class[0],0,len(classes))

            BBoxes.query.where(BBoxes.id == bbox_id).update({'age':res_class })
        else:
            classes = ['Female', 'Male']
            res_class = classes.index(res_class[0], 0, len(classes))
            BBoxes.query.where(BBoxes.id == bbox_id).update({'gender': res_class})
        try:
            db.session.commit()
        except Exception as e:
            print(f'Camera: {e}')
            db.session.rollback()
        print(f'type {self.type_classifaer} {bbox_id} Кадр обработан!')


        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)


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


    def load_model(self):
        self.path_load_model_age = 'models/vgg_16_256_Age.pth'
        self.path_load_model_gender = 'models/vgg_16_256_Gender.pth'

        if self.type_classifaer == 'age':
            self.model = vgg16_classifaer(self.path_load_model_age)
        else:
            self.model = vgg16_classifaer(self.path_load_model_gender)
        print('Инициализация модели прошла успешно')

    def up_events(self, ch, method, props, body):
        ask_js = json.loads(body)
        command, data = ask_js['command'], ask_js['data']
        messange = {}
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)
        close = False
        if command == 'delete':
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Запрос на удаление классификатора!\n')

            messange = {'command': 'info',
                        'data': {
                            'title': 'Сообщение системы',
                            'type': 'info',
                            'info': f'Классификатор {self.id_classifaer} удален!'
                        }}

            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Классификатор удален!\n')
            close = True


        self.execute_request(self.publish_messange,self.queue_out,messange=messange)

        if close:
            from main import db, Classifaer_process
            res = Classifaer_process.query.where(Classifaer_process.id == self.id_classifaer).first()
            self.execute_request(self.channel.queue_delete,self.queue_in)
            self.execute_request(self.channel.queue_delete,self.queue_out)

            db.session.delete(res)

            try:
                db.session.commit()
            except Exception as e:
                self.write_logger(path_logger, self.name_logger,
                                  f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                  f'Ошибка: {e}\n')

                print(f'Classifaer: {e}')
                db.session.rollback()

            self.exit = True
            self.execute_request(self.channel.stop_consuming)
            self.channel = None


    def connection_close(self):
        self.connection.close()
        self.connection = None


    def run(self):
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Классификатор запустился!\n')

        self.execute_request(self.publish_messange,self.up_queue, {'command': 'info',
                                              'data': {'type': 'ask',
                                                       'title': 'Сообщение системы',
                                                       'id': self.id_classifaer,
                                                       'queue_in': self.queue_in,
                                                       'queue_out': self.queue_out,
                                                       'info': f'Классификатор № {self.id_classifaer} ({self.type_classifaer}) запущен!'
                                                       }})

        self.execute_request(self.publish_messange,queue_hearbeat, {'type_proc': classifaer_script.split('.')[0] + '_'+ self.type_classifaer,
                                               'id': f'{self.id_classifaer}'})
        live = alive(host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[queue_hearbeat, {'type_proc': classifaer_script.split('.')[0] + '_' + self.type_classifaer,
                                                                          'id': f'{self.id_classifaer}',
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
                          f'Классификатор завершил работу!\n')



if __name__ == "__main__":
    try:
        id_classifaer = ''.join(sys.argv[1])
        queue = ''.join(sys.argv[2])
        id_header = ''.join(sys.argv[3])
        host = ''.join(sys.argv[4])

        n = Classifaer(id_classifaer,id_header, queue, host)
        n.run()
    except KeyboardInterrupt:
        print('Detector: Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
