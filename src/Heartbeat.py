#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
import time
import datetime
import numpy as np
from BaseClass import BaseRabbitMq,alive
import uuid
import config
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler

config.initConfig()

hearbeat = config.getCell('hearbeat')
razn = config.getCell('cnt_second_razn')
queue_hearbeat = config.getCell('queue_hearbeat')
web_queue = config.getCell('web_queue')
host = config.getCell('host')

second_resending = config.getCell('second_resending')
camera_script = config.getCell('camera')
classifaer_script = config.getCell('classifaer')
header_script = config.getCell('header')
detector_script = config.getCell('detector')
web_script = config.getCell('web')
heartbeat_script = config.getCell('heartbeat')

path_logger = os.path.join('tmp')
class HearBeat(BaseRabbitMq):
    def __init__(self, host):

        self.host = host
        super().__init__(host)

        self.table_hearbeat = {}

        self.name_logger = f"{heartbeat_script.split('.')[0]}.txt"
        self.path_logger = path_logger

        # Очередь WEB для получения сообщения о keep_alive
        self.name_queue = queue_hearbeat  # Вывести на web интерфейс
        self.execute_request(self.channel.queue_declare,queue=self.name_queue,
                                   durable=True)

        self.execute_request(self.channel.queue_declare,queue=web_queue,
                                   durable=True)
        self.execute_request(self.channel.basic_consume,
            queue=self.name_queue,
            on_message_callback=self.low_events
        )

    def low_events(self, ch, method, props, body):
        from main import db, Header_process
        try:
            ask_js = json.loads(body)
            name = ask_js['type_proc'] + "_" + str(ask_js['id'])

            cur_time = int(time.mktime(datetime.datetime.now().timetuple()))
            if name not in self.table_hearbeat:
                if ask_js['type_proc'] == header_script.split('.')[0]:
                    Header_process.query.where(Header_process.id == ask_js['id']).update({'status': 1})
                    try:
                        db.session.commit()
                    except Exception as e:
                        self.write_logger(path_logger, self.name_logger,
                                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                          f'Ошибка: {e}\n')
                        print(f'Heatbeat: {e}')
                        db.session.rollback()

                self.write_logger(path_logger, self.name_logger,
                                  f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                  f'[+] {name} зарегистрировался\n')

            else:
                self.write_logger(path_logger, self.name_logger,
                                  f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                  f'[~] {name} отметился\n')


            self.table_hearbeat[name] = {'ts': cur_time,
                                         'ts_msg': 0}

            self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

        except Exception as e:
            self.write_logger(path_logger, self.name_logger,
                              f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                              f'Ошибка: {e}\n')
            print(e)
            self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

    def check(self):
        parameters = pika.URLParameters(f'amqp://guest:guest@{self.host}/')
        ok = False
        while not ok:
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                ok = True
            except:
                ok = False

        cur_time = int(time.mktime(datetime.datetime.now().timetuple()))
        del_ = []
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Запуск <<check>>\n')

        for name in self.table_hearbeat.keys():
            if abs(self.table_hearbeat[name]['ts'] - cur_time) > razn:
                self.write_logger(path_logger, self.name_logger,
                                  f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                  f'[-] Warning {name} упал! {cur_time} - {self.table_hearbeat[name]["ts"]} '
                      f'= {abs(self.table_hearbeat[name]["ts"] - cur_time)}\n')

                del_.append(name)

        for x in del_:
            self.table_hearbeat.pop(x)


        from main import db, Camera_process, Header_process, Detector_process, Camera,Classifaer_process

        assumed_running_processes = Camera_process.query.filter(Camera_process.status > 1).all()

        for ind, x in enumerate(assumed_running_processes):
            name_proc = f'{camera_script.split(".")[0]}_{x.cam_id}'

            if (name_proc not in self.table_hearbeat) or (cur_time - self.table_hearbeat[name_proc]['ts_msg'] > second_resending and
                                                          cur_time - self.table_hearbeat[name_proc]["ts"] > razn):

                if name_proc not in self.table_hearbeat:
                    self.table_hearbeat[name_proc] = {'ts': cur_time,
                                                      'ts_msg': cur_time}
                else:
                    self.table_hearbeat[name_proc]['ts_msg'] = cur_time

                queue_header = Header_process.query.where(Header_process.id == x.id_header).first()
                name_cam = Camera.query.where(Camera.id == x.cam_id).one()

                self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                                  'data': {
                                                      'title': 'Ошибка',
                                                      'type': 'danger',
                                                      'info': f'Камера - {name_cam.name_cam} не запущена!'
                                                  }})
                self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                                  'data': {
                                                      'title': 'Сообщение системы',
                                                      'type': 'info',
                                                      'info': f'Запрос на создании камеры - {name_cam.name_cam} отпрвлен'
                                                  }})
                self.execute_request(self.publish_messange,queue_header.queue_in,
                                      {'command': 'create',
                                       'data': {'type': camera_script,
                                                'id': f'{x.cam_id}',
                                                'host': self.host}})

        assumed_running_processes = Header_process.query.filter(Header_process.status > 0).all()
        del_ = []
        for x in assumed_running_processes:
            name_proc = f'{header_script.split(".")[0]}_{x.id}'
            if name_proc not in self.table_hearbeat or \
                    abs(self.table_hearbeat[name_proc]["ts"] - cur_time) > razn:
                del_.append(name_proc)
                messange = {'command': 'info',
                            'data': {
                                'title': 'Ошибка',
                                'type': 'danger',
                                'info': f'Хедер {x.name_header} не запущен!'
                            }}
                self.execute_request(self.publish_messange,web_queue, messange)

                Header_process.query.where(Header_process.id == x.id).update({'status': 0})
                try:
                    db.session.commit()
                except Exception as e:
                    self.write_logger(path_logger, self.name_logger,
                                      f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                                      f'Ошибка: {e}')

                    db.session.rollback()


        for x in del_:
            if x in self.table_hearbeat:
                self.table_hearbeat.pop(x)


        assumed_running_processes = Detector_process.query.filter(Detector_process.status > 0).all()
        for x in assumed_running_processes:
            name_proc = f'{detector_script.split(".")[0]}_{x.id}'
            if name_proc not in self.table_hearbeat or (cur_time - self.table_hearbeat[name_proc]['ts_msg'] > second_resending and
                                                          cur_time - self.table_hearbeat[name_proc]["ts"] > razn):
                if name_proc not in self.table_hearbeat:
                    self.table_hearbeat[name_proc] = {'ts': cur_time,
                                                      'ts_msg': cur_time}
                else:
                    self.table_hearbeat[name_proc]['ts_msg'] = cur_time

                queue_header = Header_process.query.where(Header_process.id == x.id_header).first()
                self.execute_request(self.publish_messange,queue_header.queue_in,
                                      {'command': 'create',
                                       'data': {'type': detector_script,
                                                'id': f'{x.id}',
                                                'host': self.host}})
                self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                                  'data': {
                                                      'title':'Ошибка',
                                                      'type': 'danger',
                                                      'info': f'Детектор {x.id} не запущен!'
                                                  }})

        assumed_running_processes = Classifaer_process.query.filter(Classifaer_process.status > 0).all()
        for x in assumed_running_processes:
            type_classifaer = None
            if x.type_classifaer == 1:
                type_classifaer = 'age'
            else:
                type_classifaer = 'gender'

            name_proc = f'{classifaer_script.split(".")[0]}_{type_classifaer}_{x.id}'
            if name_proc not in self.table_hearbeat or (
                    cur_time - self.table_hearbeat[name_proc]['ts_msg'] > second_resending and
                    cur_time - self.table_hearbeat[name_proc]["ts"] > razn):

                if name_proc not in self.table_hearbeat:
                    self.table_hearbeat[name_proc] = {'ts': cur_time,
                                                      'ts_msg': cur_time}
                else:
                    self.table_hearbeat[name_proc]['ts_msg'] = cur_time

                queue_header = Header_process.query.where(Header_process.id == x.id_header).first()
                self.execute_request(self.publish_messange,queue_header.queue_in,
                                      {'command': 'create',
                                       'data': {'type': classifaer_script,
                                                'id': f'{x.id}',
                                                'host': self.host}})

                self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                                  'data': {
                                                      'title': 'Ошибка',
                                                      'type': 'danger',
                                                      'info': f'Классификатор {x.id} ({type_classifaer}) не запущен!'
                                                  }})

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


    def checking_the_completeness_of_the_system(self):
        set_process = set()
        for process in self.table_hearbeat.keys():
            mas = process.split('_')
            if len(mas)==2:
                name_proc = mas[0]
            else:
                name_proc = mas[0] +'_'+ mas[1]
            set_process.add(name_proc)

        if detector_script.split('.')[0] not in set_process:
            self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                              'data': {
                                                  'title': 'Ошибка',
                                                  'type': 'danger',
                                                  'info': f'Отсутствует работающий детектор! Работа системы не возможна!'
                                              }})

        if header_script.split('.')[0] not in set_process:
            self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                              'data': {
                                                  'title': 'Ошибка',
                                                  'type': 'danger',
                                                  'info': f'Отсутствует работающий хедер! Работа системы не возможна!'
                                              }})

        if classifaer_script.split('.')[0]+"_age" not in set_process:
            self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                              'data': {
                                                  'title': 'Ошибка',
                                                  'type': 'danger',
                                                  'info': f'Отсутствует работающий классификатор возраста! Работа системы не возможна!'
                                              }})

        if classifaer_script.split('.')[0]+"_gender" not in set_process:
            self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                              'data': {
                                                  'title': 'Ошибка',
                                                  'type': 'danger',
                                                  'info': f'Отсутствует работающий классификатор пола! Работа системы не возможна!'
                                              }})


    def run(self):
        self.write_logger(path_logger, self.name_logger,
                          f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                          f'Heartbeat запустился\n')

        self.execute_request(self.publish_messange,web_queue, {'command': 'info',
                                          'data': {
                                              'title': 'Инициализация',
                                              'type': 'info',
                                              'info': f'Производится загрузка системы ...'
                                          }})

        sched = BackgroundScheduler(daemon=True)
        sched.add_job(self.check, 'interval', seconds=hearbeat)
        sched.add_job(self.checking_the_completeness_of_the_system, 'interval', seconds=40)
        sched.start()

        self.execute_request(self.channel.queue_purge,queue=self.name_queue)

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
                          f'Heartbeat завершил работу\n')



if __name__ == "__main__":

    try:
        n = HearBeat(host)
        n.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
