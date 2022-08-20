#!/usr/bin/python3
import json
import os
from scipy.spatial import distance
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon as Pol
from multiprocessing import Pool
from datetime import datetime
import numpy as np
import KalmanFilter
import time

EPS = 0.32


def cur_time():
    return datetime.now().strftime("%m/%d/%Y, %H:%M:%S")


def compare_features(f1, f2):
    return 1.0 - distance.cosine(f1, f2)


def load_bboxes(cam_id):
    from main import db, BBoxes
    if cam_id is None:
        res = BBoxes.query.filter_by(type=0).order_by(BBoxes.id).all()
    else:
        res = BBoxes.query.filter_by(cam_id=cam_id, type=0).order_by(BBoxes.id).all()
    return res


def load_people_map(cam_id=None):
    from main import db, PeopleMap, People, BBoxes
    t_res = People.query.filter_by(clss=0).all()
    people_map = []
    max_man_id = 0
    for cur in t_res:
        if cam_id is None:
            res = PeopleMap.query.filter_by(person_id=cur.id).all()
        else:
            res = PeopleMap.query.join(BBoxes, PeopleMap.bbox_id == BBoxes.id).\
                filter(BBoxes.cam_id == cam_id, PeopleMap.person_id == cur.id).all()
        if len(res) == 0:
            continue
        person = res[-1]
        people_map.append(person)
        max_man_id = max(max_man_id, cur.id)

    return people_map, max_man_id + 1


def load_camera_polygons(cam_id=None):
    from main import db, Polygon
    if cam_id is not None:
        res = Polygon.query.filter_by(cam_id=cam_id).order_by(Polygon.id).all()
    else:
        res = Polygon.query.order_by(Polygon.id).all()
    for row in res:
        if type(row.polygon) is list:
            return res
        new_polygon = []
        for point in row.polygon['polygon']:
            new_polygon.append((point['x'], point['y']))
        row.polygon = new_polygon
    return res

def load_camera(cam_id=None):
    from main import db, Camera
    if cam_id is not None:
        res = Camera.query.filter_by(cam_id=cam_id).order_by(Camera.id).all()
    else:
        res = Camera.query.order_by(Camera.id).all()
    return res[0]

# def compare_people(cur_bbox, cur_features, people_map, bboxes):
#     flag_new_people = True
#     max_similarity = 0
#     man_id = -1
#     bboxes_id = -1
#     for people in people_map:
#         temp_bbox = []
#         find_box = 1
#         if people.bbox_id in bboxes:
#             temp_bbox = bboxes[people.bbox_id]
#             find_box = 0
#         if find_box or cur_bbox.id == temp_bbox[0].id:
#             continue
#         features = temp_bbox[1]
#         similarity = compare_features(cur_features, features)
#         if similarity > max_similarity:
#             man_id = people.person_id
#             bboxes_id = people.bbox_id
#             max_similarity = similarity
#     if max_similarity > EPS:
#         flag_new_people = False
#
#     return flag_new_people, man_id, bboxes_id


def insert_people_map(man_id, bboxes_id, area_id):
    from main import db, PeopleMap
    new_people_map = PeopleMap(area_id=area_id, bbox_id=bboxes_id, person_id=man_id)
    # print('new_people_map',new_people_map)
    try:
        db.session.add(new_people_map)
        # db.session.commit()
        print(f"People_map {man_id} loaded")
    except:
        db.session.rollback()
        print(f"People_map {man_id} already exists")

    return


def is_polygon(x, y, points):
    zone = Pol(points)
    return zone.contains(Point((x, y)))


# def which_area(cur_bbox, camera):
#     for cur_camera in camera:
#         if cur_camera.cam_id != cur_bbox.cam_id:
#             continue
#
#         x, y = (cur_bbox.r + cur_bbox.l) / 2, (cur_bbox.b + cur_bbox.t) / 2
#         if is_polygon(x, y, cur_camera.polygon):
#             return cur_camera.area_id
#     return 1e9 + cur_bbox.cam_id

def which_area(row, col,cam_id, camera):
    for cur_camera in camera:
        if cur_camera.cam_id != cam_id:
            continue

        #x, y = (cur_bbox.r + cur_bbox.l) / 2, (cur_bbox.b + cur_bbox.t) / 2
        if is_polygon(col, row, cur_camera.polygon):
            return cur_camera.area_id
    return 1e9 + cam_id


# def insert_bboxes(start_bbox, finish_bbox):
#     if start_bbox.cam_id != finish_bbox.cam_id:
#         return
#     else:
#         x0, y0 = (start_bbox.r + start_bbox.l) / 2, (start_bbox.b + start_bbox.t) / 2
#         x1, y1 = (finish_bbox.r + finish_bbox.l) / 2, (finish_bbox.b + finish_bbox.t) / 2
#         start_bbox.processed = 1
#         start_bbox.direction = [(x0, y0), (x1, y1)]
#         # нужно изменить start_bbox в BBoxes
#         from main import db, BBoxes
#         res = BBoxes.query.filter_by(id=finish_bbox.id).update({"processed": 1, "direction": [(x0, y0), (x1, y1)]})
#         # db.session.commit()
#         print(f"Bbox {start_bbox.id} updated")
#
#     return


# def find_bbox_by_id(bbox_id, bboxes):
#     for cur_bbox in bboxes:
#         if cur_bbox.id == bbox_id:
#             return cur_bbox


def insert_people(cam_id):
    # add new person and return id
    # clss = 0
    from main import db, People
    new_people = People(clss=0,cam_id=cam_id)
    try:
        db.session.add(new_people)
        # db.session.commit()
        print(f"New people {new_people.id} loaded")
    except:
        db.session.rollback()
        print(f"New people {new_people.id} already exists")
    res = People.query.filter_by(clss=0, cam_id=cam_id).order_by(People.id).all()
    return res[-1].id

def get_last_man_id(cam_id):
    from main import db, People
    res = People.query.filter_by(clss=0,cam_id = cam_id).order_by(People.id).all()
    if len(res)==0:
        return 1
    return res[-1].id + 1

# def get_good_bbox(bbox):
#     return bbox, np.array(json.loads(json.loads(bbox.features)))


# def analyze_camera(cam_id):
#     from main import db
#     camera = load_camera(cam_id)
#     bboxes = load_bboxes(cam_id)
#
#     bboxes_map = dict([(bbox.id, get_good_bbox(bbox)) for bbox in bboxes])
#     people_map, max_man_id = load_people_map(cam_id)
#     bbox_count = len(bboxes_map)
#
#     print(f"{cur_time()} Start processing {bbox_count} boxes for camera #{cam_id}")
#     for i, (_, (cur_bbox, cur_feature)) in enumerate(bboxes_map.items()):
#         if cur_bbox.processed == 1:
#             continue
#         if i > 0 and i % 50 == 0:
#             print(f"{cur_time()} processed {i + 1}/{bbox_count} boxes for camera #{cam_id}")
#             try:
#                 db.session.commit()
#             except:
#                 db.session.rollback()
#         flag_new_people, man_id, bboxes_id = compare_people(cur_bbox, cur_feature, people_map, bboxes_map)
#         if flag_new_people:
#             man_id = insert_people()
#             insert_bboxes(cur_bbox, cur_bbox)
#         else:
#             insert_bboxes(find_bbox_by_id(bboxes_id, bboxes), cur_bbox)
#
#         area_id = which_area(cur_bbox, camera)
#         insert_people_map(man_id, cur_bbox.id, area_id)
#
#     db.session.commit()
#     print(f"{cur_time()} Finished processing {bbox_count} boxes for camera #{cam_id}")

def prediction_further_path(kf, track, count_frame, cnt_predict):
    for id_person in track.keys():
        if track[id_person]['last_frame'] - count_frame < cnt_predict:
            upgrade_mean, upgrade_covariance = kf.update(track[id_person]['mean'],
                                                         track[id_person]['covariance'],
                                                         np.array([track[id_person]['x'], track[id_person]['y'],
                                                                   track[id_person]['mean'][2],
                                                                   track[id_person]['mean'][3]]))
            track[id_person]['mean'], track[id_person][
                'covariance'] = kf.predict(upgrade_mean, upgrade_covariance)
            track[id_person]['x'] = int(track[id_person]['mean'][0])
            track[id_person]['y'] = int(track[id_person]['mean'][1])

def get_all_dist(res, count_frame):
    global min_square_bbox
    global cnt_to_del
    global track
    all_dist = [] # Массив дистанций от каждой точки до каждой
    points = set() # Множество точек центров Bboxes
    for bbox in res:
        if (bbox.r - bbox.l) * (bbox.b - bbox.t) < min_square_bbox:
            continue

        bbox_x = bbox.l + (bbox.r - bbox.l) // 2
        bbox_y = bbox.t + (bbox.b - bbox.t) // 2
        points.add((bbox_x, bbox_y,
                    (bbox.r - bbox.l)/(bbox.b - bbox.t),
                    (bbox.b - bbox.t),
                    bbox.id))
        id_person_del = []

        for id_person in track.keys():
            if count_frame - track[id_person]['last_frame'] > cnt_to_del:
                id_person_del.append(id_person)
                continue

            dist = distance.euclidean((bbox_x, bbox_y), (track[id_person]['x'], track[id_person]['y']))
            all_dist.append([dist, {'bbox_x': bbox_x, 'bbox_y': bbox_y,
                                    'track_x': track[id_person]['x'], 'track_y': track[id_person]['y'],
                                    'bbox_l': bbox.l, 'bbox_r': bbox.r,
                                    'bbox_b': bbox.b, 'bbox_t': bbox.t,
                                    'id_person': id_person,
                                    'id_bboxes': bbox.id}])

        # Удаление всех точек которые давно не использовались
        for id_person in id_person_del:
            track.pop(id_person)

    return points, all_dist

def analyze_camera(cam_id):
    from main import db, BBoxes
    global min_square_bbox
    global cnt_to_del
    global track
    # Загрузка полигонов
    camera_polygons = load_camera_polygons(cam_id)
    # Загрузка информации о камере
    camera = load_camera(cam_id)
    # Через сколько кадров удалять метку бокса в случае неактивности
    cnt_to_del = 30
    count_frame = 0
    # Отслеживание перемещения BBoxes
    track = dict()
    track[1e9] = {'x': 1e9,
                  'y': 1e9,
                  'last_frame': 0}
    # Количество предсказаний после потери bbox
    cnt_predict = 15
    # Максимальная дистанция между боксами px
    max_dist = 200
    # Минимальная площадь бокса
    min_square_bbox = 500
    kf = KalmanFilter.KalmanFilter()

    # cnt_person = get_last_man_id(cam_id)

    cur_ts_unix= int(time.mktime(camera.start_ts.timetuple()))
    end_ts_unix = int(time.mktime(camera.end_ts.timetuple()))

    cnt_frame = 5
    while cur_ts_unix <= end_ts_unix:
        # Запрос всех боксов камеры в момент времени
        ts_ = datetime.fromtimestamp(cur_ts_unix).strftime("%Y-%m-%d %H:%M:%S")
        query_bboxes = BBoxes.query.filter_by(cam_id=cam_id, frame_id=cnt_frame).order_by(BBoxes.id).all()
        # Нахождение дистанции для каждого бокса
        points, all_dist = get_all_dist(query_bboxes,count_frame)
        all_dist.sort(key=lambda x: x[0])

        used = set()

        if count_frame == 0:
            track.pop(1e9)

        cnt_obn = 0;
        for cur_dist in all_dist:
            if (cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y']) in used or \
                    (cur_dist[1]['track_x'], cur_dist[1]['track_y']) in used:
                continue

            if cur_dist[0] > max_dist:
                break
            cnt_obn+=1
            used.add((cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y']))
            used.add((cur_dist[1]['track_x'], cur_dist[1]['track_y']))

            points.remove((cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y'],
                           (cur_dist[1]['bbox_r'] - cur_dist[1]['bbox_l']) / (
                                       cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t']),
                           cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t'],
                           cur_dist[1]['id_bboxes']))

            update_mean, update_covariance = kf.update(track[cur_dist[1]['id_person']]['mean'],
                                                         track[cur_dist[1]['id_person']]['covariance'],
                                                         np.array([cur_dist[1]['bbox_x'], cur_dist[1]['bbox_y'],
                                                                   (cur_dist[1]['bbox_r'] - cur_dist[1]['bbox_l']) / (
                                                                               cur_dist[1]['bbox_b'] - cur_dist[1][
                                                                           'bbox_t']),
                                                                   (cur_dist[1]['bbox_b'] - cur_dist[1]['bbox_t'])]))

            area_id = which_area(cur_dist[1]['bbox_x'],
                                 cur_dist[1]['bbox_y'],
                                 cam_id,
                                 camera_polygons)

            insert_people_map(cur_dist[1]['id_person'],
                              cur_dist[1]['id_bboxes'],
                              area_id)

            # # Предсказание нового местарасположения
            # track[cur_dist[1]['id_person']]['mean'], track[cur_dist[1]['id_person']][
            #     'covariance'] = kf.predict(upgrade_mean, upgrade_covariance)
            # # Обновление информации
            track[cur_dist[1]['id_person']]['mean'] = update_mean
            track[cur_dist[1]['id_person']]['covariance'] = update_covariance
            track[cur_dist[1]['id_person']]['x'] = int(update_mean[0])
            track[cur_dist[1]['id_person']]['y'] = int(update_mean[1])
            track[cur_dist[1]['id_person']]['last_frame'] += 1

        print(f'Количество обнаруженных старых {cnt_obn}')
        cnt_new = 0
        for cur_points in points:
            cnt_new+=1
            mean, covariance = kf.initiate(
                np.array([cur_points[0], cur_points[1],
                          cur_points[2],
                          cur_points[3]]))
            # predict_mean, predict_covariance = kf.predict(mean, covariance)
            #man_id = get_last_man_id(cam_id)
            man_id = insert_people(cam_id)
            track[man_id] = {'x': int(mean[0]),
                                 'y': int(mean[1]),
                                 'person_id': man_id,
                                 'mean': mean,
                                 'covariance': covariance,
                                 'last_frame': count_frame}

            area_id = which_area(cur_points[0],
                                 cur_points[1],
                                 cam_id,
                                 camera_polygons)

            insert_people_map(man_id,
                              cur_points[-1],
                              area_id)

        print(f'Количество новых {cnt_new}')
        prediction_further_path(kf, track, count_frame, cnt_predict)

        if count_frame > 0 and count_frame % 3 == 0:
            print(f"{cur_time()} processed {count_frame} frame for camera #{cam_id}")
            try:
                db.session.commit()
            except:
                db.session.rollback()

        cur_ts_unix += camera.fps
        cnt_frame += camera.fps
        if len(query_bboxes) > 0:
            cur_ts_unix = int(time.mktime(query_bboxes[0].ts.timetuple()))
        count_frame += 1

    db.session.commit()
    print(f"{cur_time()} Finished processing for camera #{cam_id}")

def analize():
    from main import db, Polygon
    # camerasId = [x for x, in Polygon.query.with_entities(Polygon.cam_id).distinct().all()]
    camerasId = range(3,4)
    for cam_id in camerasId:
        analyze_camera(cam_id)


if __name__ == "__main__":
    analize()
    pass
