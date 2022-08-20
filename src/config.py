# -*- coding: utf-8 -*-
import sys

module = sys.modules[__name__]


def setCell(name, value):
    module.table[name] = value


def getCell(name):
    return module.table.get(name)


def initConfig():
    module.table = {}
    setCell('file_roads', 'data_/roads.txt')
    setCell('path_info_roads', 'data_/')


    # Очередь для передачи hearbeat
    setCell('queue_hearbeat','hearbeat')


    # Очередь для передачи сообщений дочернему процессу WEB
    setCell('com_queue', 'com_queue')
    # Очередь для передачи сообщений непосредственно в Web
    setCell('web_queue', 'queue_web')
    # Очередь для передачи сообщений классификатору возраста
    setCell('queue_classifaer_age', 'queue_classifaer_age')
    # Очередь для передачи сообщений классификатору пола
    setCell('queue_classifaer_gender', 'queue_classifaer_gender')

    # Очередь для трансляции
    setCell('stream_queue', 'stream_queue')


    # Адрес для подключения rabbitmq
    setCell('host','my-rabbit')
    # setCell('host','localhost')

    # Очередь для общения камер с детекторами
    setCell('queue_cam_to_detector', 'queue_frames')


    # Частота отправки сообщений hearbeat
    setCell('hearbeat', 15)


    # Соотношение название команды и вызываемого скрипта
    setCell('web', 'WEB.py')
    setCell('heartbeat', 'Heartbeat.py')
    setCell('camera', 'Camera.py')
    setCell('header', 'Header.py')
    setCell('classifaer', 'Classifaer.py')
    setCell('detector', 'Detector.py')
    setCell('analizer', 'Analizer_rabbit.py')


    # Через сколько секунд отсутствия сообщений считать что процесс упал
    setCell('cnt_second_razn', 30)
    setCell('second_resending', 20)

