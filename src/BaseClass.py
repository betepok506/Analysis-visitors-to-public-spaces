#!/usr/bin/env python
import pika, sys, os
import cv2 as cv
import json
import numpy as np
import time
import config

config.initConfig()
host = config.getCell('host')

class BaseRabbitMq(object):
    def __init__(self,host):
        parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')

        ok = False
        while not ok:
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                ok = True
            except:
                ok = False


    def write_logger(self, path_logger, name_logger,str_):
        with open(os.path.join(path_logger, name_logger), 'a+') as f:
            f.write(str_)


    def on_request(self):
        pass

    def call(self):
        pass

    def publish_messange(self, routing_key, messange):
        try:
            self.channel.basic_publish(exchange='',
                                       routing_key=routing_key,
                                       body=json.dumps(messange))
        except:
            self.channel.close()
            parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')

            ok = False
            while not ok:
                try:
                    self.connection = pika.BlockingConnection(parameters)
                    self.channel = self.connection.channel()
                    ok = True
                except:
                    ok = False

            self.channel.basic_publish(exchange='',
                                       routing_key=routing_key,
                                       body=json.dumps(messange))
class alive(BaseRabbitMq):
    def __init__(self,url_host):
        super().__init__(url_host)

    def keep_alive(self, routing_key, message):
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=json.dumps(message))
        except:
            parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
            ok = False
            while not ok:
                try:
                    self.connection = pika.BlockingConnection(parameters)
                    self.channel = self.connection.channel()
                    ok = True
                except:
                    ok = False

            self.channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=json.dumps(message))