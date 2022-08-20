#!/usr/bin/python3
import subprocess

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, redirect, url_for, session, copy_current_request_context
import os
# from frames_detector import process_file
from flask_sqlalchemy import SQLAlchemy
import hashlib
import magic
import cv2 as cv
import time
import datetime
from analizer import analize
import numpy as np
from datetime import date
from statistics import statistics
from BaseClass import BaseRabbitMq
from flask import render_template, url_for, jsonify, flash
import load_data
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput, Button
from bokeh.io import curdoc
from bokeh.resources import INLINE
from bokeh.models import Range1d
from bokeh.events import PressUp
from bokeh.transform import cumsum
from bokeh.palettes import *
import pandas as pd
from math import pi
from bokeh.embed import components, json_item
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, CustomJS, DateRangeSlider
import uuid
from flask import Response
import re

from threading import Lock
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import config
from sqlalchemy import and_, or_, distinct
config.initConfig()

import pika
# import eventlet
# from eventlet import tpool
# eventlet.monkey_patch()
# gevent.monkey_patch()

from pathlib import Path
from engineio.payload import Payload

Payload.max_decode_packets = 50
app = Flask(__name__)

app.secret_key = 'park'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_DATABASE_URI') or "postgresql://postgres:park@localhost:6000/park"
# docker
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
#     'SQLALCHEMY_DATABASE_URI') or "postgresql://postgres:park@127.0.0.1:3876/park"

app.config['SQLALCHEMY_POOL_SIZE'] = 1000
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 1000
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 60000
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_EXTENSIONS'] = ['.avi','.mp4']
app.config['UPLOAD_PATH'] = 'video'

db = SQLAlchemy(app)

# async_mode = None
async_mode = 'threading'

thread = None
thread_lock = Lock()

process_main_header = True
# url connect to RabbtiMQ
config.initConfig()

# host = 'localhost'
web_queue = config.getCell('web_queue')

camera_script = config.getCell('camera')
classifaer_script = config.getCell('classifaer')
detector_script = config.getCell('detector')
web_script = config.getCell('web')
heartbeat_script = config.getCell('heartbeat')
host = config.getCell('host')
header_script = config.getCell('header')

LONG_TIME_STREAM = 1 * 60
classes_age = ['Children', 'Adults', 'Elderly', 'Undefined ']
classes_gender = ['Female', 'Male', 'Undefined' ]
PATH_VIDEO_SAVE = os.path.join('./src','static','tmp')


socketio = SocketIO(app, async_mode=async_mode, message_queue=f'amqp://{host}/')


# ,message_queue=f'amqp://guest:guest@{host}/'

class BBoxes(db.Model):
    __tablename__ = 'bboxes'

    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.Integer)
    l = db.Column(db.Integer)
    r = db.Column(db.Integer)
    t = db.Column(db.Integer)
    b = db.Column(db.Integer)
    ts = db.Column(db.TIMESTAMP)
    type = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    age = db.Column(db.Integer)
    # features = db.Column(db.JSON)
    # direction = db.Column(db.JSON)
    processed = db.Column(db.Integer)
    frame_id = db.Column(db.Integer)

    def __init__(self, cam_id, l, r, t, b, ts, tp, gender, age,  frame_id, processed=0):
        self.cam_id = cam_id
        self.l = l
        self.r = r
        self.t = t
        self.b = b
        self.ts = ts
        self.type = tp
        self.gender = gender
        self.age = age
        # self.features = features
        # self.direction = direction
        self.processed = processed
        self.frame_id = frame_id

    def __repr__(self):
        return f"<id: {self.id}, cam_id: {self.cam_id}, l: {self.l}, r: {self.r}, t: {self.t}, b: {self.b}, frame_id: {self.frame_id}>"


class Header_process(db.Model):
    __tablename__ = 'header_process'

    id = db.Column(db.Integer, primary_key=True)
    name_header = db.Column(db.String)
    # header_id = db.Column(db.Integer)
    queue_in = db.Column(db.String)
    queue_out = db.Column(db.String)
    queue_header = db.Column(db.String)
    status = db.Column(db.Integer)

    def __init__(self, name_header,
                 # header_id,
                 queue_header, queue_in, queue_out, status):
        self.name_header = name_header
        # self.header_id = header_id
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.queue_header = queue_header
        self.status = status

    def __repr__(self):
        return f"<id: {self.id}, name_header: {self.name_header}, queue_in: {self.queue_in}, \
        queue_out: {self.queue_out}, status: {self.status}, queue_header: {self.queue_header}>"


class Polygons_map(db.Model):
    __tablename__ = 'polygons_map'

    id = db.Column(db.Integer, primary_key=True)
    polygons = db.Column(db.String)
    area_id = db.Column(db.Integer)


    def __init__(self, polygons, area_id):
        self.polygons = polygons
        self.area_id = area_id


    def __repr__(self):
        return f"<id: {self.id}, polygons: {self.polygons}, area_id: {self.area_id}>"


class Video(db.Model):
    __tablename__ = 'video'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String)
    video_md5 = db.Column(db.String)
    processed = db.Column(db.Integer)

    def __init__(self, filename, video_md5, processed=0):
        self.filename = filename
        self.video_md5 = video_md5
        self.processed = processed

    def __repr__(self):
        return f"<id: {self.id}, filename: {self.filename}, video_md5: {self.video_md5}, video_md5: {self.video_md5}>"


class PeopleMap(db.Model):
    __tablename__ = 'people_map'

    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer)
    bbox_id = db.Column(db.Integer)
    person_id = db.Column(db.Integer)

    def __init__(self, area_id, bbox_id, person_id):
        self.area_id = area_id
        self.bbox_id = bbox_id
        self.person_id = person_id

    def __repr__(self):
        return f"<id: {self.id}, area_id: {self.area_id}, bbox_id: {self.bbox_id}, person_id: {self.person_id}>"


class Polygon(db.Model):
    __tablename__ = 'polygons'

    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer)
    polygon = db.Column(db.JSON)
    cam_id = db.Column(db.Integer)

    def __init__(self, area_id, polygon, cam_id):
        self.area_id = area_id
        self.polygon = polygon
        self.cam_id = cam_id

    def __repr__(self):
        return f"<id: {self.id}, area_id: {self.area_id}, cam_id: {self.cam_id}, polygon: {self.polygon}>"


class Camera_process(db.Model):
    __tablename__ = 'camera_process'

    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.Integer)
    queue_in = db.Column(db.String)
    queue_out = db.Column(db.String)
    status = db.Column(db.Integer)
    id_header = db.Column(db.Integer)
    queue_callback = db.Column(db.String)
    queue_analizer_out = db.Column(db.String)
    queue_analizer_in = db.Column(db.String)

    def __init__(self, cam_id, id_header, queue_in, queue_out, status, queue_callback, queue_analizer_out,
                 queue_analizer_in):
        self.id_header = id_header
        self.cam_id = cam_id
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.status = status
        self.queue_callback = queue_callback
        self.queue_analizer_out = queue_analizer_out
        self.queue_analizer_in = queue_analizer_in

    def __repr__(self):
        return f"<id: {self.id},cam_id:{self.cam_id}, id_header: {self.id_header}, queue_callback: {self.queue_callback}  \
                queue_in: {self.queue_in}, queue_out: {self.queue_out}, status: {self.status}, queue_analizer_out: {self.queue_analizer_out}" \
               f"queue_analizer_in: {self.queue_analizer_in}>"


class AgeGroups(db.Model):
    __tablename__ = 'age_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<id: {self.id}, name: {self.name}>"


class BBoxTypes(db.Model):
    __tablename__ = 'bbox_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<id: {self.id}, name: {self.name}>"


class People(db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    clss = db.Column(db.Integer)
    cam_id = db.Column(db.Integer)

    def __init__(self, clss, cam_id):
        self.clss = clss
        self.cam_id = cam_id

    def __repr__(self):
        return f"<id: {self.id}, class: {self.clss}, cam_id: {self.cam_id}>"


class Camera(db.Model):
    __tablename__ = 'camera'

    id = db.Column(db.Integer, primary_key=True)
    cur_frame = db.Column(db.Integer)
    all_frame = db.Column(db.Integer)
    fps = db.Column(db.Integer)
    start_ts = db.Column(db.TIMESTAMP)
    fps_video = db.Column(db.Integer)
    max_dist_between_bbox = db.Column(db.Integer)
    min_square_bbox = db.Column(db.Integer)
    cnt_fps_del = db.Column(db.Integer)
    url = db.Column(db.String)
    name_cam = db.Column(db.String)

    def __init__(self, cur_frame, fps_video, all_frame, fps, start_ts,
                 max_dist_between_bbox,
                 min_square_bbox,
                 cnt_fps_del,
                 url,
                 name_cam):
        self.name_cam = name_cam
        self.fps = fps
        self.fps_video = fps_video
        self.start_ts = start_ts
        self.cur_frame = cur_frame
        self.all_frame = all_frame
        self.max_dist_between_bbox = max_dist_between_bbox
        self.min_square_bbox = min_square_bbox
        self.cnt_fps_del = cnt_fps_del
        self.url = url

    def __repr__(self):
        return f"<id: {self.id}, name_cam: {self.name_cam}, start_ts: {self.start_ts}, cur_frame: {self.cur_frame}, \
        all_frame: {self.all_frame}, max_dist_between_bbox: {self.max_dist_between_bbox}, min_square_bbox: {self.min_square_bbox}, \
        cnt_fps_del: {self.cnt_fps_del}, url: {self.url}, fps_video: {self.fps_video}>"


class Detector_process(db.Model):
    __tablename__ = 'detector_process'

    id = db.Column(db.Integer, primary_key=True)
    queue_in = db.Column(db.String)
    queue_out = db.Column(db.String)
    status = db.Column(db.Integer)
    id_header = db.Column(db.Integer)

    def __init__(self, id_header, queue_in, queue_out, status):
        self.id_header = id_header
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.status = status

    def __repr__(self):
        return f"<id: {self.id}, id_header: {self.id_header}  \
                queue_in: {self.queue_in}, queue_out: {self.queue_out}, status: {self.status}>"


class Classifaer_process(db.Model):
    __tablename__ = 'classifaer_process'

    id = db.Column(db.Integer, primary_key=True)
    queue_in = db.Column(db.String)
    queue_out = db.Column(db.String)
    status = db.Column(db.Integer)
    id_header = db.Column(db.Integer)
    type_classifaer = db.Column(db.Integer)

    def __init__(self, id_header, queue_in, queue_out, status, type_classifaer):
        self.id_header = id_header
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.status = status
        self.type_classifaer = type_classifaer

    def __repr__(self):
        return f"<id: {self.id}, id_header: {self.id_header}  \
                queue_in: {self.queue_in}, queue_out: {self.queue_out}, status: {self.status}, " \
               f"type_classifaer: {self.type_classifaer}>"


class Default_params(db.Model):
    __tablename__ = 'default_params'

    id = db.Column(db.Integer, primary_key=True)
    num_frame_delete = db.Column(db.Integer)
    max_dist_between_bbox = db.Column(db.Integer)
    min_square_bbox = db.Column(db.Integer)
    proc_freq = db.Column(db.Integer)

    def __init__(self, num_frame_delete, max_dist_between_bbox, min_square_bbox, proc_freq):
        self.num_frame_delete = num_frame_delete
        self.max_dist_between_bbox = max_dist_between_bbox
        self.min_square_bbox = min_square_bbox
        self.proc_freq = proc_freq

    def __repr__(self):
        return f"<id: {self.id}, num_frame_delete: {self.num_frame_delete}, max_dist_between_bbox: {self.max_dist_between_bbox}  \
                min_square_bbox: {self.min_square_bbox}, proc_freq: {self.proc_freq}>"


# def md5(fname):
#     hash_md5 = hashlib.md5()
#     with open(fname, "rb") as f:
#         for chunk in iter(lambda: f.read(4096), b""):
#             hash_md5.update(chunk)
#     return hash_md5.hexdigest()



def create_graphs(area_idx, info_roads, val_start, val_end, min_ts, max_ts):
    # zones = np.array(info_roads)[:, 1]
    # # zones = PeopleMap.query.distinct(PeopleMap.area_id).all()
    # # zones = np.array([str(x.area_id) for x in zones])
    # colors = np.array(info_roads)[:, 2]
    # zone_idx = np.where(zones == str(area_idx))
    # try:
    #     zone_color = colors[zone_idx][0]
    # except:
    #     zone_color = colors[0][0]
    rad = 0.4
    color_plt = load_data.color_plt
    left_wedges_height = 420

    callback = CustomJS(code="""
     var str = window.location.href;
     var path = str.split('?')[0];
     var start_ts = '0';
     var end_ts = '1'; 
     try {
         start_ts = document.getElementsByClassName('noUi-handle-lower')[0].getAttribute('aria-valuetext');
         end_ts = document.getElementsByClassName('noUi-handle-upper')[0].getAttribute('aria-valuetext'); 
     }
     catch (e) {
       console.log(e);
     }     
     
     var new_path = path + '?start_ts=' + start_ts + '&end_ts=' + end_ts;
     window.location.replace(new_path);
     """)



    update_info_button = Button(label="Обновить информацию", button_type="success", sizing_mode='stretch_both',
                                margin=[-5, 5, 5, 5])
    update_info_button.js_on_click(callback)

    date_range_slider = DateRangeSlider(
        value=(
            val_start,
            val_end
        ),
        format='%d.%m.%Y %H:%M:%S',
        start=min_ts,
        end=max_ts,
        default_size=720,
        sizing_mode='stretch_width',
        css_classes=['time_slider']
    )

    dict_data_graph = statistics(area_idx, val_start, val_end, 6)
    ######################################################################################

    #  Круговая диаграмма
    #     x = {'Взрослые': random.randint(0, 100), 'Дети': random.randint(0, 100), 'Пожилые': random.randint(0, 100), 'Неопределенный': random.randint(0, 10)}
    x = dict_data_graph['stat_age']
    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    data['color'] =  ['#689dd9','#92f0b8','#cd8ae5']#,'#ff85c0']#color_plt[len(x)]
    graph_wedge_age = figure(
        plot_height=left_wedges_height,
        title="Данные по возрасту посетителей",
        toolbar_location=None,
        sizing_mode='scale_both',
        tools="hover",
        tooltips="@country: @value"
    )
    graph_wedge_age.wedge(
        x=0, y=1, radius=rad,
        start_angle=cumsum('angle', include_zero=True),
        end_angle=cumsum('angle'),
        line_color="white",
        fill_color='color',
        legend='country',
        source=data
    )

    ######################################################################################

    #     x = {'Мужчины': random.randint(0, 100), 'Женщины': random.randint(0, 100), 'Неопределенный': random.randint(0, 10)}
    x = dict_data_graph['stat_gender']
    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    # data['color'] = color_plt[len(x)]
    data['color'] = ['#689dd9', '#92f0b8', '#cd8ae5']
    graph_wedge_gender = figure(
        plot_height=left_wedges_height,
        title="Данные по полу посетителей",
        toolbar_location=None,
        sizing_mode='scale_both',
        tools="hover",
        tooltips="@country: @value"
    )
    graph_wedge_gender.wedge(
        x=0, y=1, radius=rad,
        start_angle=cumsum('angle', include_zero=True),
        end_angle=cumsum('angle'),
        line_color="white",
        fill_color='color',
        legend='country',
        source=data
    )

    ######################################################################################

    #     x = {'Пешеходы': random.randint(0, 100), 'С собаками': random.randint(0, 100), 'Велосипедисты': random.randint(0, 100), 'Неопределенный тип': random.randint(0, 10)}
    x = dict_data_graph['stat_type_pos_all']
    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    # data['color'] = color_plt[len(x)]
    data['color'] = ['#689dd9', '#92f0b8', '#cd8ae5', '#ff85c0']
    graph_wedge_inventory = figure(
        plot_height=left_wedges_height,
        title="Данные по типу посетителей",
        toolbar_location=None,
        sizing_mode='scale_both',
        tools="hover",
        tooltips="@country: @value"
    )
    graph_wedge_inventory.wedge(
        x=0, y=1, radius=rad,
        start_angle=cumsum('angle', include_zero=True),
        end_angle=cumsum('angle'),
        line_color="white",
        fill_color='color',
        legend='country',
        source=data
    )

    ######################################################################################

    # Статистика по дням

    #     x1 = ["07.09.2021 10:19", "07.09.2021 10:24", "07.09.2021 10:29", "07.09.2021 10:34", "07.09.2021 10:39"]
    # "20.09.2021", "21.09.2021", "22.09.2021", "23.09.2021", "24.09.2021"]
    x1 = dict_data_graph['x']
    #     y1 = []
    #     for i in range(len(x1)):
    #         y1.append(random.randint(10, 100))
    y1 = dict_data_graph['stat_people_rep']
    bar_day = figure(
        x_range=x1,
        title="Статистика по временным интервалам",
        x_axis_label="Дата",
        y_axis_label="Кол-во посетителей",
        plot_height=270,
        sizing_mode='scale_both'
    )
    bar_day.vbar(
        x=x1,
        top=y1,
        width=0.5,
        bottom=0,

        #         color=color_plt[color_plt_id][central_bar_idx]
    )
    bar_day.xaxis.major_label_orientation = 0.3

    ######################################################################################

    #     x1 = [16,7,5,11,20, 16,7,5,11,20, 16,7,5]
    x1 = dict_data_graph['stat_area']
    bar_plase = figure(
        y_range=dict_data_graph['zones'],
        title="Статистика по зонам",
        y_axis_label="Зона",
        x_axis_label="Кол-во посетителей",
        plot_height=1420,
        sizing_mode='scale_both'
    )
    bar_plase.hbar(
        y=dict_data_graph['zones'],
        right=x1,
        height=0.5,
        left=0,
        # color=colors
    )

    ######################################################################################

    # Столбчатая диаграмма по дням
    script_stat_day, div_stat_day = components(bar_day)

    # По возрастному составу
    script_wedge_age, div_wedge_age = components(graph_wedge_age)

    # По полу
    script_wedge_gender, div_wedge_gender = components(graph_wedge_gender)

    # Круговая диаграмма по инвентарю
    script_wedge_inventory, div_wedge_inventory = components(graph_wedge_inventory)

    # Столбчатая диаграмма по местем в парке
    script_stat_plase, div_stat_plase = components(bar_plase)

    # Dateslider
    script_slider, div_slider = components(date_range_slider)

    # Dateslider
    script_update_info_button, div_update_info_button = components(update_info_button)

    return [script_stat_day, div_stat_day, \
            script_wedge_age, div_wedge_age, \
            script_wedge_inventory, div_wedge_inventory, \
            script_stat_plase, div_stat_plase, \
            script_wedge_gender, div_wedge_gender, \
            script_slider, div_slider, \
            script_update_info_button, div_update_info_button
            ]


@app.route('/')
@app.route('/index')
def index():
    # Загрузить все зоны
    polygons = Polygons_map.query.all()
    # info_roads = load_data.load_roads()
    num_road = 100001
    stat_road = load_data.load_stat_road(num_road)

    try:
        min_ts = BBoxes.query.order_by(BBoxes.ts).first().ts
        max_ts = BBoxes.query.order_by(BBoxes.ts.desc()).first().ts
    except:
        min_ts = datetime.datetime.now()
        max_ts = (datetime.datetime.now() + datetime.timedelta(0, 1))
        print(f'{min_ts} {max_ts}')

    start_ts = request.args.get('start_ts')
    end_ts = request.args.get('end_ts')
    cnt_int = request.args.get('cnt_interval')
    try:
        start_ts_unix = datetime.datetime.utcfromtimestamp(int(float(start_ts)) // 1000)
        print(start_ts_unix)
    except Exception as e:
        print(e)
        start_ts_unix = min_ts

    try:
        end_ts_unix = datetime.datetime.utcfromtimestamp(int(float(end_ts)) // 1000)
        print(end_ts_unix)
    except Exception as e:
        print(e)
        end_ts_unix = max_ts
    # list_camers = db.session.query(Camera.id, Camera.name_cam).all()
    list_camers = [x[0] for x in db.session.query(PeopleMap.area_id).distinct().all()]
    list_camers.sort()
    graphs = create_graphs(num_road, polygons, start_ts_unix, end_ts_unix, min_ts, max_ts)
    return render_template(
        'index.html',
        roads=polygons,
        num_road=100001,
        stat_road=stat_road,
        graphs=graphs,
        list_camers=list_camers
    )

    # return render_template('index.html')


@app.route('/<int:num_road>')
def statistic_road(num_road):
    info_roads = load_data.load_roads()
    stat_road = load_data.load_stat_road(num_road)

    min_ts = BBoxes.query.order_by(BBoxes.ts).first().ts
    max_ts = BBoxes.query.order_by(BBoxes.ts.desc()).first().ts

    start_ts = request.args.get('start_ts')
    end_ts = request.args.get('end_ts')

    try:
        start_ts_unix = datetime.datetime.utcfromtimestamp(int(float(start_ts)) // 1000)
        print(start_ts_unix)
    except Exception as e:
        print(e)
        start_ts_unix = min_ts

    try:
        end_ts_unix = datetime.datetime.utcfromtimestamp(int(float(end_ts)) // 1000)
        print(end_ts_unix)
    except Exception as e:
        print(e)
        end_ts_unix = max_ts

    # list_camers = db.session.query(Camera.id, Camera.name_cam).all()
    list_camers = [x[0] for x in db.session.query(PeopleMap.area_id).distinct().all()]
    list_camers.sort()
    polygons = Polygons_map.query.all()
    graphs = create_graphs(num_road, polygons, start_ts_unix, end_ts_unix, min_ts, max_ts)
    return render_template(
        'index.html',
        roads=polygons,
        num_road=num_road,
        stat_road=stat_road,
        graphs=graphs,
        list_camers = list_camers
    )



def get_default_par():
    res = Default_params.query.order_by(Default_params.id.desc()).first()
    return res


@app.route('/camers', methods=['GET', 'POST'])
def camers():
    Path(os.path.join(PATH_VIDEO_SAVE,'video')).mkdir(parents=True, exist_ok=True)

    list_camers = Camera.query.order_by(Camera.id).all()
    status_camers = Camera_process.query.order_by(Camera_process.id).all()

    dict_start_end_ts_by_cam = dict()
    for cur_cam in list_camers:
        try:
            start_ts = BBoxes.query.filter_by(cam_id=cur_cam.id).order_by(BBoxes.ts.asc()).first().ts
            end_ts = BBoxes.query.filter_by(cam_id=cur_cam.id).order_by(BBoxes.ts.desc()).first().ts
            dict_start_end_ts_by_cam[cur_cam.id] = {'start_ts':start_ts.strftime("%Y-%m-%d %H-%M-%S"),
                                                 'end_ts':end_ts.strftime("%Y-%m-%d %H-%M-%S")}
        except Exception as e:
            dict_start_end_ts_by_cam[cur_cam.id] = {'start_ts':-1,
                                                 'end_ts':-1}
            print(e)
            continue

    list_header = [x.name_header for x in Header_process.query.all()]
    default_params = get_default_par()

    # Информация о наличии видео
    list_video = []
    for file in os.listdir(os.path.join(PATH_VIDEO_SAVE,'video')):
        list_video.append(int(file.split('_')[0]))

    return render_template(
        'camers_list.html',
        list_camers=list_camers,
        status_camers=status_camers,
        list_header=list_header,
        default_params=default_params,
        list_video = list_video,
        dict_start_end_ts_by_cam = dict_start_end_ts_by_cam)


@app.route('/headers', methods=['GET', 'POST'])
def headers():
    list_headers = Header_process.query.all()
    return render_template(
        'headers_list.html',
        list_headers=list_headers)


@app.route('/detectors', methods=['GET', 'POST'])
def detectors():
    list_detectors = Detector_process.query.all()
    list_header = [x.name_header for x in Header_process.query.all()]
    return render_template(
        'detectors_list.html',
        list_detectors=list_detectors,
        list_header=list_header)


@app.route('/classifaers', methods=['GET', 'POST'])
def classifaers():
    list_classifaers = Classifaer_process.query.all()
    list_header = [x.name_header for x in Header_process.query.all()]
    return render_template(
        'classifaers_list.html',
        list_classifaers=list_classifaers,
        list_header=list_header)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    default_value = Default_params.query.order_by(Default_params.id).first()
    polygons = Polygons_map.query.all()
    return render_template(
        'settings.html',
        default_value=default_value,
        pol = polygons
    )


def publish_messange_rabbitmq(action, type_proc, id_):
    import json
    socketio.sleep(0)
    ok = False
    parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
    while not ok:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            ok = True
        except:
            ok = False

    queue = get_queue_header(type_proc, id_)

    if action == 'run':
        type_proc = camera_script

    messange = {'command': action,
                'data': {'type': type_proc,
                         'id': id_,
                         'host': host}}

    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=json.dumps(messange))
    print('Сообщение отправлено!')
    channel.close()


def delete_queue(queues):
    socketio.sleep(0)
    parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
    ok = False
    while not ok:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            ok = True
        except:
            ok = False

    for queue in queues:
        channel.queue_delete(queue)
    channel.close()


def get_queue_header(type_proc, id):
    if type_proc == camera_script.split('.')[0]:
        res = Camera_process.query.where(Camera_process.cam_id == int(id)).first()

    elif type_proc == classifaer_script.split('.')[0]:
        res = Classifaer_process.query.where(Classifaer_process.id == int(id)).first()

    elif type_proc == detector_script.split('.')[0]:
        res = Detector_process.query.where(Detector_process.id == int(id)).first()

    elif type_proc == header_script.split('.')[0]:
        res = Header_process.query.where(Header_process.id == int(id)).first()
        return res.queue_in

    if res == None:
        emit('my_response', {'data': 'Процесс еще не запущен, для дальнейшего взаимодействия дождитель его запсука!',
                             'title': 'Предупреждение',
                             'type_messange': f'warning'})
        return
    res = Header_process.query.where(Header_process.id == res.id_header).first()
    return res.queue_in


def get_status_process(name_proc, id):
    res = []
    print(f'Get_status_process id: {id}')
    if name_proc == camera_script.split('.')[0]:
        res = Camera_process.query.where(Camera_process.cam_id == int(id)).first()
    elif name_proc == classifaer_script.split('.')[0]:
        res = Classifaer_process.query.where(Classifaer_process.id == int(id)).first()
    elif name_proc == detector_script.split('.')[0]:
        res = Detector_process.query.where(Detector_process.id == int(id)).first()
    elif name_proc == header_script.split('.')[0]:
        res = Header_process.query.where(Header_process.id == int(id)).first()

    if res == None:
        return -1
    return res.status


@socketio.event
def events_process_old(messange):
    action = messange['button'].split('_')[0]
    name_proc, id_ = messange['id'].split('_')
    id_=int(id_)
    status_process = get_status_process(name_proc, id_)
    # Отключить запущенный процесс
    if action == 'stop':
        if status_process == 0:
            emit('my_response', {'data': 'Камера уже останевлена!',
                                 'title': 'Предупреждение',
                                 'type_messange': f'warning'})
            return

        print(f'Остановка камеры {messange}')

    elif action == 'delete':

        if status_process == 0 and name_proc == camera_script.split('.')[0]:
            res = Camera.query.where(Camera.id == id_).one()
            db.session.delete(res)

            res = Camera_process.query.where(Camera_process.cam_id == id_).one()
            # Удаление очередей камеры
            mas_queue = [res.queue_in,res.queue_out,res.queue_callback]
            delete_queue(mas_queue)
            db.session.delete(res)

            try:
                db.session.commit()
                emit('my_response', {'data': 'Камера удалена',
                                     'title': 'Сообщение системы',
                                     'type_messange': f'info'})
            except Exception as e:
                emit('my_response', {'data': f'Ошибка удаление камеры: {e}',
                                    'title': 'Ошибка',
                                    'type_messange': f'danger'})
                print(f'Camera: {e}')
                db.session.rollback()
            return

        print(f'Удаление камеры {messange}')
    # Редактирование настроек камеры
    elif action == 'editing':
        res = Camera.query.where(Camera.id == id_).first()
        print(f'Редактирование камеры {messange}')
        socketio.emit('get_info2web',
                      {'id': res.id,
                       'name_cam': res.name_cam,
                       'start_ts': res.start_ts,
                       'fps': res.fps,
                       'polygons': res.polygons,
                       'max_dist_between_bbox': res.max_dist_between_bbox,
                       'min_square_bbox': res.min_square_bbox,
                       'cnt_fps_del': res.cnt_fps_del
                       })
        return

    # Создание камеры
    elif action == 'run':
        if status_process == 2:
            emit('my_response', {'data': 'Камера уже запущена!',
                                 'title': 'Предупреждение',
                                 'type_messange': f'warning'})
            return

        print('Создание камеры')
    # Сохранение измененных настроек
    elif action == 'save':
        data = messange['data']
        for x in data.keys():
            if data[x] == '':
                data[x] = None
        Camera.query.where(Camera.id == id_).update({'name_cam': data['name_cam'],
                                                       'fps': data['fps'],
                                                       'start_ts': data['ts'],
                                                       # 'polygons': data['polygons'],
                                                       'max_dist_between_bbox': data['max_dist_bboxes'],
                                                       'min_square_bbox': data['min_square_bboxes'],
                                                       'cnt_fps_del': data['time_delete_tracking']
                                                       })
        try:
            db.session.commit()
        except Exception as e:
            print(f'Camera: {e}')
            db.session.rollback()

        socketio.emit('my_response',
                      {'data': "Изменения сохранены!",
                       'title': 'Сообщение системы',
                       'type_messange': f'info'})
        return
    else:
        return
    publish_messange_rabbitmq(action, name_proc, id_)


@app.route('/events_process', methods=['POST', 'GET'])
def events_process():
    if request.method == 'POST':
        action, id_ = request.form['action'],  int(request.form['cam_id'])
        name_proc = camera_script.split('.')[0]

        status_process = get_status_process(name_proc, id_)
        if action == 'stop':
            if status_process == 0:
                socketio.emit('my_response', {'data': 'Камера уже останевлена!',
                                              'title': 'Предупреждение',
                                     'type_messange': f'warning'})
                return Flask.response_class(status=200)

        elif action == 'delete':
            if status_process <= 0 and name_proc == camera_script.split('.')[0]:
                res = Camera.query.where(Camera.id == id_).one()
                db.session.delete(res)

                res = Camera_process.query.where(Camera_process.cam_id == id_).one()
                # Удаление очередей камеры
                mas_queue = [res.queue_in,res.queue_out,res.queue_callback]
                delete_queue(mas_queue)
                db.session.delete(res)

                try:
                    db.session.commit()
                    socketio.emit('my_response', {'data': 'Камера удалена',
                                                  'title': 'Сообщение системы',
                                                 'type_messange': f'info'})
                except Exception as e:
                    socketio.emit('my_response', {'data': f'Ошибка удаление камеры: {e}',
                                                  'title': 'Ошибка',
                                                 'type_messange': f'danger'})
                    print(f'Camera: {e}')
                    db.session.rollback()

                return Flask.response_class(status=200)

        # Создание камеры
        elif action == 'run':
            if status_process == 2:
                socketio.emit('my_response', {'data': 'Камера уже запущена!',
                                              'title': 'Предупреждение',
                                                'type_messange': f'warning'})
                return Flask.response_class(status=200)

            print('Создание камеры')

        # Сохранение измененных настроек
        elif action == 'save':
            import json
            data = json.loads(request.form['data'])
            for x in data.keys():
                if data[x] == '':
                    data[x] = None

            Camera.query.where(Camera.id == id_).update({'name_cam': data['name_cam'],
                                                           'fps': data['fps'],
                                                           'start_ts':  datetime.datetime.strptime(data['ts'], '%Y-%m-%d %H:%M:%S'),
                                                           'max_dist_between_bbox': data['max_dist_bboxes'],
                                                           'min_square_bbox': data['min_square_bboxes'],
                                                           'cnt_fps_del': data['time_delete_tracking']
                                                           })
            try:
                db.session.commit()
            except Exception as e:
                print(f'Camera: {e}')
                db.session.rollback()

            socketio.emit('my_response',
                          {'data': "Изменения сохранены!",
                           'title': 'Сообщение системы',
                           'type_messange': f'info'})

            return Flask.response_class(status=200)
        else:
            return Flask.response_class(status=200)

        publish_messange_rabbitmq(action, name_proc, id_)
        return Flask.response_class(status=200)


    else:
        action = request.args.get('action')
        id_cam = request.args.get('id_cam')
        # Редактирование настроек камеры
        if action == 'editing':
            import json

            res = Camera.query.where(Camera.id == id_cam).first()
            return json.dumps({'id': res.id,
                               'name_cam': res.name_cam,
                               'start_ts': res.start_ts,
                               'fps': res.fps,
                               'max_dist_between_bbox': res.max_dist_between_bbox,
                               'min_square_bbox': res.min_square_bbox,
                               'cnt_fps_del': res.cnt_fps_del
                               },default=str), 200, {'ContentType': 'application/json'}
        else:
            id_cam = request.args.get('id_cam')
            rez = Polygon.query.where(Polygon.cam_id == id_cam).all()
            polygons_ = [x.polygon for x in rez]
            area_id_ = [x.area_id for x in rez]
            import json
            return json.dumps({'polygons':polygons_,'area_id':area_id_}), 200, {'ContentType':'application/json'}


@app.route('/save_polygons', methods=['POST'])
def save_polygons():
    import json
    polygons, area_id = json.loads(request.form['polygons']), json.loads(request.form['area_id'])
    cam_id = int(request.form['cam_id'])
    for ind in range(len(polygons)):
        new_polygons = Polygon(
            cam_id=cam_id,
            polygon=polygons[ind],
            area_id=int(area_id[ind])
        )
        db.session.add(new_polygons)
        if ind % 5 == 0:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                emit('my_response', {'data': f'Ошбика добавление полигона в базу данных! Ошибка: {e}',
                                     'title': 'Ошибка',
                                     'type_messange': f'danger'})
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        emit('my_response', {'data': f'Ошбика добавление полигона в базу данных! Ошибка: {e}',
                             'title': 'Ошибка',
                             'type_messange': f'danger'})

    return Flask.response_class(status=200)


@app.route('/save_polygons_map', methods=['POST'])
def save_polygons_map():
    import json
    list_polygons = json.loads(request.form['list_polygons'])
    Polygons_map.query.delete()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    for cur_pol in list_polygons:
        # res = Polygons_map.query.where(Polygons_map.area_id == cur_pol['area_id']).all()
        res = []
        if len(res) == 0:
            new_polygons = Polygons_map(
                polygons=cur_pol['polygons'],
                area_id=cur_pol['area_id']
            )
            try:
                db.session.add(new_polygons)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                emit('my_response', {'data': f'Ошбика добавление полигона в базу данных! Ошибка: {e}',
                                     'title': 'Ошибка',
                                     'type_messange': f'danger'})
        else:
            Polygons_map.query.where(Polygons_map.area_id == cur_pol['area_id']).update({'polygons': cur_pol['polygons']})


    return Flask.response_class(status=200)


@socketio.event
def create_detector(messange):
    import json
    import uuid
    name_header = messange['header']

    res = Header_process.query.where(Header_process.name_header == name_header).first()
    new_detector = Detector_process(
        queue_in=str(uuid.uuid4()),
        queue_out=str(uuid.uuid4()),
        status=1,
        id_header=res.id,
    )
    try:
        db.session.add(new_detector)
        db.session.commit()
        print(f"Detector: Info load Detector")
    except Exception as e:
        db.session.rollback()
        emit('my_response', {'data': f'Ошбика добавление детектора в базу данных! Ошибка: {e}',
                             'title': 'Ошибка',
                             'type_messange': f'danger'})

    socketio.sleep(0)
    parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
    ok = False
    while not ok:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            ok = True
        except:
            ok = False

    detector_id = Detector_process.query.order_by(Detector_process.id.desc()).first().id
    channel.queue_declare(queue=res.queue_in, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=res.queue_in,
                          body=json.dumps({'command': 'create',
                                           'data': {'type': detector_script,
                                                    'id': str(detector_id),
                                                    'info': '',
                                                    'host': host
                                                    }}))


@socketio.event
def create_classifaer(messange):
    import json
    import uuid
    name_header = messange['header']
    type_classifaer = messange['type_classifaer']

    res = Header_process.query.where(Header_process.name_header == name_header).first()
    new_classifaer = Classifaer_process(
        queue_in=str(uuid.uuid4()),
        queue_out=str(uuid.uuid4()),
        status=1,
        id_header=res.id,
        type_classifaer=type_classifaer
    )
    try:
        db.session.add(new_classifaer)
        db.session.commit()
        print(f"Classifaer: Info load Classifaer")
    except Exception as e:
        db.session.rollback()
        emit('my_response', {'data': f'Ошбика добавление классификатора в базу данных! Ошибка: {e}',
                             'title': 'Ошибка',
                             'type_messange': f'danger'})

    socketio.sleep(0)
    parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
    ok = False
    while not ok:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            ok = True
        except:
            ok = False

    classifaer_id = Classifaer_process.query.order_by(Classifaer_process.id.desc()).first().id
    channel.queue_declare(queue=res.queue_in, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=res.queue_in,
                          body=json.dumps({'command': 'create',
                                           'data': {'type': classifaer_script,
                                                    'id': str(classifaer_id),
                                                    'info': '',
                                                    'host': host
                                                    }}))


@app.route('/create_camera', methods=['POST'])
def create_camera():
    all_frame = 0
    if request.form['url'] == '':
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                socketio.emit('my_response', {'data': f'Данный формат не поддерживается!',
                                              'title': 'Ошибка',
                                              'type_messange': f'danger'})
                return redirect(url_for('index'))

            filename = str(uuid.uuid4()) + file_ext
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            filename = os.path.join(app.config['UPLOAD_PATH'], filename)
        else:
            socketio.emit('my_response', {'data': f'Некорректное имя файла!',
                                          'title': 'Ошибка',
                                          'type_messange': f'danger'})
            return

        date_time = datetime.datetime.strptime(request.form['ts'], '%Y-%m-%d %H-%M-%S')
    else:
        filename = request.form['url']
        date_time = datetime.datetime.now()

    cap = cv.VideoCapture(filename)
    if cap.isOpened() == None:
        socketio.emit('my_response', {'data': f'Не удалось открыть видео/видеопоток!',
                                      'title': 'Ошибка',
                                      'type_messange': f'danger'})
        return

    (major_ver, minor_ver, subminor_ver) = (cv.__version__).split('.')
    if int(major_ver) < 3:
        fps = cap.get(cv.cv.CV_CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else:
        fps = cap.get(cv.CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    if request.form['url'] == '':
        all_frame = 1
        # all_frame = cap.get(cv.CAP_PROP_FRAME_COUNT)

    new_camera = Camera(
        name_cam=request.form['name_cam'],
        fps=request.form['fps'],
        start_ts=date_time,
        url=filename,
        fps_video = max(20,min(30,fps)),
        max_dist_between_bbox=request.form['max_dist_bboxes'],
        min_square_bbox=request.form['min_square_bboxes'],
        cnt_fps_del=request.form['time_delete_tracking'],
        cur_frame=0,
        all_frame=all_frame
    )

    ok = True
    try:
        db.session.add(new_camera)
        db.session.commit()
    except Exception as e:
        socketio.emit('my_response', {'data': f'Ошибка добавления камеры в базу данных! {e} Камера не создана!',
                                      'title': 'Ошибка',
                                      'type_messange': f'danger'})
        db.session.rollback()
        ok = False
        print(e)

    if ok:
        import json
        name_header = request.form['name_header']
        res = Header_process.query.where(Header_process.name_header == name_header).first()
        cam_id = Camera.query.order_by(Camera.id.desc()).first().id

        socketio.emit('my_response', {'data': f'Индекс, добавляемой камеры! {cam_id}',
                                      'title': 'Сообщение системы',
                                      'type_messange': f'info'})
        socketio.sleep(0)
        parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
        ok = False
        while not ok:
            try:
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                ok = True
            except:
                ok = False

        channel.queue_declare(queue=res.queue_in, durable=True)
        channel.basic_publish(exchange='',
                              routing_key=res.queue_in,
                              body=json.dumps({'command': 'create',
                                               'data': {'type': camera_script,
                                                        'id': f'{cam_id}',
                                                        'info': '',
                                                        'host': host
                                                        }}))
    return Flask.response_class(status=200)


@app.route('/delete_polygons', methods=['POST'])
def delete_polygons():
    area_id = request.form['area_id']
    res = Polygons_map.query.where(Polygons_map.area_id == area_id).first()
    if res == None:
        return Flask.response_class(status=200)

    db.session.delete(res)

    try:
        db.session.commit()
    except Exception as e:
        print(f'Detector: {e}')
        db.session.rollback()

    return Flask.response_class(status=200)


@app.route('/progress/<cam_id>')
def progress(cam_id):
    import json
    cam_id, ts_start, ts_end = cam_id.split('_')
    cam_id = int(cam_id)
    FPS = Camera.query.where(Camera.id == cam_id).first()

    if ts_start == -1:
        end_frame = BBoxes.query.filter_by(cam_id=cam_id).order_by(BBoxes.frame_id.desc()).first().frame_id

        start_frame = end_frame - LONG_TIME_STREAM * FPS.fps_video
        cnt_frame = LONG_TIME_STREAM * FPS.fps_video / FPS.fps
    else:
        ts_start = datetime.datetime.strptime(ts_start, '%Y-%m-%d %H-%M-%S')
        ts_end = datetime.datetime.strptime(ts_end, '%Y-%m-%d %H-%M-%S')
        try:
            start_frame = BBoxes.query.where(BBoxes.ts >= ts_start).order_by(BBoxes.frame_id.asc()).first().frame_id
        except:
            vid_dict = {}

            vid_dict[0] = 101
            ret_string = "data:" + json.dumps(vid_dict) + "\n\n"
            print(ret_string)
            # yield ret_string
            return Response('Error', mimetype='text/event-stream')

        try:
            end_frame = BBoxes.query.where(BBoxes.ts <= ts_end).order_by(BBoxes.frame_id.desc()).first().frame_id
        except:
            vid_dict = {}

            vid_dict[0] = 101
            ret_string = "data:" + json.dumps(vid_dict) + "\n\n"
            print(ret_string)
            # yield ret_string
            return Response('Error', mimetype='text/event-stream')

        cnt_frame = (end_frame - start_frame) / FPS.fps
    print(f'Start frame: {start_frame} end_frame: {end_frame} cnt_frame: {cnt_frame}')

    Path(os.path.join(PATH_VIDEO_SAVE,'video')).mkdir(parents=True, exist_ok=True)

    def create_video(cam_id,start_frame, end_frame, FPS, cnt_frame):
        import json
        cur_frame = 0

        frame_size = (480,320)
        writer = cv.VideoWriter(os.path.join(PATH_VIDEO_SAVE,'video',f'{cam_id}_create.webm'),
                                cv.VideoWriter_fourcc(*'vp80'),
                                # cv.VideoWriter_fourcc(*'MP4V'),
                                # -1,
                                # cv.VideoWriter_fourcc(*'X264'),
                                # cv.VideoWriter_fourcc(*'H264'),
                                # cv.VideoWriter_fourcc(*'XVID'),
                                5,frame_size)
        start_frame = max(0, start_frame)
        for cur_img in range(start_frame, end_frame, FPS.fps):
            if os.path.exists(os.path.join('tmp', f'{cam_id}' , f'{cur_img}.jpg')):
                frame = cv.imread(os.path.join('tmp', f'{cam_id}' , f'{cur_img}.jpg'))

                res = BBoxes.query.filter_by(cam_id=cam_id, frame_id=cur_img).order_by(BBoxes.id).all()

                for bbox in res:
                    query = PeopleMap.query.filter_by(bbox_id=bbox.id).all()
                    if len(query) == 0:
                        continue
                    query_people = query[0]
                    cnt = 15
                    cv.rectangle(frame, (bbox.l, bbox.t), (bbox.r, bbox.b),
                                 ((255 + cnt * query_people.person_id) % 256,
                                  (255 + 2 * cnt * query_people.person_id) % 256,
                                  (255 + 7 * cnt * query_people.person_id) % 256),
                                 thickness=2)

                    cv.putText(img=frame,
                               text=classes_age[bbox.age],
                               org=(bbox.l, bbox.t + 50),
                               fontFace=cv.FONT_HERSHEY_PLAIN,
                               fontScale=2,
                               color=((255 + cnt * query_people.person_id) % 256,
                                      (255 + 2 * cnt * query_people.person_id) % 256,
                                      (255 + 7 * cnt * query_people.person_id) % 256),
                               thickness=2)

                    cv.putText(img=frame,
                               text=classes_gender[bbox.gender],
                               org=(bbox.l, bbox.t + 10),
                               fontFace=cv.FONT_HERSHEY_PLAIN,
                               fontScale=2,
                               color=((255 + cnt * query_people.person_id) % 256,
                                      (255 + 2 * cnt * query_people.person_id) % 256,
                                      (255 + 7 * cnt * query_people.person_id) % 256),
                               thickness=2)

                frame = cv.resize(frame,frame_size)
                writer.write(frame)
                cur_frame +=1
                vid_dict = {}

                vid_dict[0] = int(cur_frame/cnt_frame * 100)

                ret_string = "data:" + json.dumps(vid_dict) + "\n\n"

                yield ret_string

        vid_dict = {}

        vid_dict[0] = 100

        ret_string = "data:" + json.dumps(vid_dict) + "\n\n"
        yield ret_string
        writer.release()


    return Response(create_video(cam_id,start_frame, end_frame, FPS, cnt_frame), mimetype='text/event-stream')

@app.route('/editing_setting', methods=['POST'])
def editing_setting():
    num_frame_delete = int(request.form['time_delete_tracking'])
    max_dist_between_bbox = int(request.form['max_dist_bboxes'])
    min_square_bbox = int(request.form['min_square_bboxes'])
    proc_freq = int(request.form['fps'])
    Default_params.query.where(Default_params.id == 1).update({'num_frame_delete': num_frame_delete,
                                                               'max_dist_between_bbox': max_dist_between_bbox,
                                                               'min_square_bbox': min_square_bbox,
                                                               'proc_freq': proc_freq})

    try:
        db.session.commit()
    except Exception as e:
        socketio.emit('my_response', {'data': f'Не удалось сохранить настройки! Ошибка {e}!',
                                      'title': 'Ошибка',
                                      'type_messange': f'danger'})
        db.session.rollback()
        ok = False
        print(e)

    return Flask.response_class(status=200)


@app.route('/load_map', methods=['POST'])
def load_map():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext != '.svg':
            socketio.emit('my_response', {'data': f'Данный формат не поддерживается!',
                                          'title': 'Ошибка',
                                          'type_messange': f'danger'})
            return redirect(url_for('index'))

        filename = 'Karta' + file_ext
        uploaded_file.save(os.path.join('./src/static/img', filename))
    else:
        socketio.emit('my_response', {'data': f'Некорректное имя файла!',
                                      'title': 'Ошибка',
                                      'type_messange': f'danger'})
    return Flask.response_class(status=200)


@app.route('/load_markup', methods=['POST'])
def load_markup():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext != '.txt':
            socketio.emit('my_response', {'data': f'Данный формат не поддерживается!',
                                          'title':'Ошибка',
                                          'type_messange': f'danger'})
            return redirect(url_for('index'))

        filename = 'markup' + file_ext
        uploaded_file.save(os.path.join('./data_', filename))
    else:
        socketio.emit('my_response', {'data': f'Некорректное имя файла!',
                                      'title': 'Ошибка',
                                      'type_messange': f'danger'})
    return Flask.response_class(status=200)


# @socketio.event
# def my_ping():
#     emit('my_pong')


# @socketio.event
# def connect():
#     emit('my_response', {'data': 'Connected', 'count': 0})


def start_background_thread():
    socketio.sleep(0)
    parameters = pika.URLParameters(f'amqp://guest:guest@{host}/')
    ok = False
    while not ok:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            ok = True
        except:
            ok = False

    channel.queue_declare(queue=web_queue,
                          durable=True)

    channel.basic_consume(on_message_callback=on_message,
                          queue=web_queue)

    print(' [*] Waiting for messages:')
    channel.start_consuming()




def on_message(channel, method, properties, body):
    import json
    channel.basic_ack(delivery_tag=method.delivery_tag)

    ask_js = json.loads(str(body.decode('utf8').replace("'", '"')))
    command, data = ask_js['command'], ask_js['data']

    socketio.emit('my_response', {'title': f'{data["title"]}',
                                  'data': f'{data["info"]}',
                                  'type_messange': f'{data["type"]}'})



def my_background():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=start_background_thread)
    print('Background thread started')


def init_default_params():
    new_params = Default_params(
        num_frame_delete=5,
        max_dist_between_bbox=100,
        min_square_bbox=500,
        proc_freq=5
    )
    try:
        db.session.add(new_params)
        db.session.commit()
    except Exception as e:
        socketio.emit('my_response',
                      {'data': "Ошибка добавления камеры!", 'count': 0})
        db.session.rollback()
        print(e)


if __name__ == "__main__":
    # init_default_params()
    # exit(0)
    my_background()

    process = subprocess.Popen(["python",
                                f'src/{web_script}'])

    result = subprocess.Popen(["python",
                               f'./src/{heartbeat_script}'])

    # app.run(host='0.0.0.0', port=8282, debug=True, use_reloader=False, threaded = True)
    socketio.run(app, host='0.0.0.0', port=8282, debug=False)
#     app.run(host='0.0.0.0', port=8282, debug=True)
