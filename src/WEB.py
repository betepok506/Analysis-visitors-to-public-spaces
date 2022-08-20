#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
import numpy as np
from BaseClass import BaseRabbitMq, alive
from apscheduler.schedulers.background import BackgroundScheduler
import config
import time
import uuid
import subprocess

config.initConfig()

hearbeat = config.getCell('hearbeat')
web_queue = config.getCell('web_queue')
queue_hearbeat = config.getCell('queue_hearbeat')
com_queue = config.getCell('com_queue')
host = config.getCell('host')

class WEB(BaseRabbitMq):
    def __init__(self, host):

        super().__init__(host)
        self.host = host

        # Очередь WEB для получения сообщения о keep_alive
        self.name_queue = com_queue  # Вывести на web интерфейс
        self.hearbeat_queue = queue_hearbeat
        self.execute_request(self.channel.queue_declare,queue=self.name_queue,
                                   durable=True)

        self.execute_request(self.channel.queue_declare,queue=web_queue,
                                   durable=True)

        self.execute_request(self.channel.queue_declare,queue=self.hearbeat_queue,
                                   durable=True)

        self.execute_request(self.channel.basic_consume,
            queue=self.name_queue,
            on_message_callback=self.low_events
        )

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
        ask_js = json.loads(body)
        command, data = ask_js['command'], ask_js['data']
        self.execute_request(ch.basic_ack,delivery_tag=method.delivery_tag)

        # Подтверждение создания хедера
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
                self.queue_in = data['queue_in']

                self.execute_request(self.channel.basic_publish,exchange='',
                                           routing_key=web_queue,
                                           body=json.dumps({'command': 'info',
                                                            'data': {'title':'Успешно',
                                                                    'type': 'success',
                                                                     'info': data['info']}}))


            else:
                self.execute_request(self.channel.basic_publish,exchange='',
                                           routing_key=web_queue,
                                           body=json.dumps(ask_js))


        else:
            self.execute_request(self.channel.basic_publish,exchange='',
                                       routing_key=web_queue,
                                       body=json.dumps(ask_js))


    def run_header(self):
        result = subprocess.Popen(["python",
                                   "./src/Header.py",
                                   'Main_header',  # name header
                                   self.name_queue,
                                   f'{host}'])


    def run(self):
        self.run_header()

        live = alive(host)
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(live.keep_alive, 'interval', args=[queue_hearbeat, {'type_proc': 'web',
                                                                    'id': f'1',
                                                                    'id_header': 0,
                                                                    'name': 'SubWeb'
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


if __name__ == "__main__":
    try:
        n = WEB(host)
        n.run()
    except KeyboardInterrupt:
        print('Web: Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
