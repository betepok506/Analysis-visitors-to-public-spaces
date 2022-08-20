#!/usr/bin/python3
import os
from scipy.spatial import distance
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon as Pol
from datetime import datetime, date, time
import time
from sqlalchemy import between

# start_time - начальное время подсчета
# end_time - конечное время подсчета статистики
# area_id - зона подсчета статистики
# num_range - количество периодов столбчатой диаграммы
# mas_plase - массив мест
# def statistics(start_time, end_time, area_id, mas_area, num_range=6):
#     from main import db, BBoxes, People, PeopleMap
#     from sqlalchemy import between
#     res = db.session.query(People.id, PeopleMap.area_id, BBoxes.ts, BBoxes.type, BBoxes.gender, BBoxes.age).filter(PeopleMap.person_id == People.id).filter(BBoxes.id == PeopleMap.bbox_id).\
#           where(between(BBoxes.ts, str(start_time),
#           str(end_time))).order_by(People.id).all()
#
#     dec_area = {}
#     for ind, area in enumerate(mas_area):
#         dec_area.setdefault(area,ind)
#
#     k = 2 # Количество считаемых значений
#     num_unique_people = 0 # Кол-во уникальных
#     rep_people = 0 # Сколько вообще прошло
#     max_people = 0 # Сколько максимум одновременно находилось в зоне
#     num_bicycle = 0
#     num_dog = 0
#
#     # New
#     # Запрос для полного диапазона
#     start_ = datetime.strptime(str(start_time).split('.')[0], "%Y-%m-%d %H:%M:%S").timestamp()
#     # start_ = start_time.timestamp()
#     # print(type(end_time))
#     end_ = datetime.strptime(str(end_time).split('.')[0], "%Y-%m-%d %H:%M:%S").timestamp()
#     # end_ = end_time.timestamp()
#     per = (end_ - start_) // num_range #
#
#     # Результат
#     out_graph_day = [[0 for col in range(k)] for row in range(num_range)]
#     out_graph_inv = [[0 for col in range(2)] for row in range(num_range)]
#     all_area = [0] * len(mas_area)
#     all_gender = [0] * 3
#     all_age = [0] * 4
#     # Подсчет типов посетителей
#     all_dog = 0
#     all_bicycle = 0
#     all_people = 0
#     add_bicycle = 0
#     add_dog = 0
#     add_people = 0
#     # Подсчет женщин и мужчин по флагу add_people
#     # Подсчет по зонам
#     last_area = -1
#
#     # Разбить на мелкие
#     end_per_time = start_ + per
#     start_per_time = start_
#
#     last_people = -1
#     man_in_zone = 0
#     dog_in_zone = False
#     bicycle_in_zone = False
#     add_people_area = False
#     viz_zone = False
#     ind = 0
#     add_all_zones = False
#     flag_add_people = False
#     # print(dec_area)
#     last_zone = -1
#     # print(out_graph_day)
#     for people_id, ar_id, ts, clss, gender, age in res:
#         ts = ts.timestamp()
#
#         if people_id != last_people:
#             # Обработка людей
#             if not viz_zone and last_people != -1 and man_in_zone == 1:
#                 num_unique_people = 1
#
#             if not flag_add_people and last_people != -1 and man_in_zone == 1:
#                 rep_people += 1
#
#             # График людей
#
#
#             out_graph_day[ind][0] += num_unique_people
#             out_graph_day[ind][1] += rep_people
#
#             # График Инвентаря
#             out_graph_inv[ind][0] += num_bicycle
#             out_graph_inv[ind][1] += num_dog
#
#             # Обработка инвенторя
#             if dog_in_zone:
#                 add_dog = 1
#             if bicycle_in_zone:
#                 add_bicycle = 1
#             if man_in_zone:
#                 add_people = 1
#
#             # Подсчет для круговой диаграмма типов посетителей
#             all_dog += add_dog
#             all_bicycle += add_bicycle
#             all_people += add_people
#
#             # Подсчет мужчин и женщин и ошибок
#             if add_people:
#                 all_gender[gender - 1] += 1
#                 all_age[age - 1] += 1
#
#             # if not add_people_area:
#             #     if last_area!=-1:
#             #         all_area[dec_area[str(last_area)]]+=1
#
#             ind = 0
#             last_people = people_id
#             # Начинаю считать заного для новолго промежутка времени
#             #
#             num_unique_people = 0
#             rep_people = 0
#
#             num_dog = 0
#             num_bicycle = 0
#
#             # ind += 1
#             flag_add_people = False
#             viz_zone = False
#             add_people_area = False
#             man_in_zone = 0
#             last_zone = -1
#             end_per_time = start_ + per
#             start_per_time = start_
#
#         # Переход на новый период
#         if ts > end_per_time:
#             # График людей
#             out_graph_day[ind][0] += num_unique_people
#             out_graph_day[ind][1] += rep_people
#
#             # График Инвентаря
#             out_graph_inv[ind][0] += num_bicycle
#             out_graph_inv[ind][1] += num_dog
#
#             # Начинаю считать заного для новолго промежутка времени
#             num_unique_people = 0
#             rep_people = 0
#
#             num_dog = 0
#             num_bicycle = 0
#
#             ind += 1
#             flag_add_people = False
#             viz_zone = False
#
#             end_per_time += per
#             start_per_time += per
#
#             while end_per_time < ts:
#                 end_per_time += per
#                 start_per_time += per
#
#
#             if end_per_time > end_:
#                 end_per_time = start_ + per
#                 start_per_time = start_
#                 ind = 0
#
#             last_zone = -1
#
#
#         if ts < start_per_time and ar_id == area_id:
#             if clss == 0:
#                 man_in_zone = 1
#             if clss == 1:
#                 bicycle_in_zone = 1
#             if clss == 16:
#                 dog_in_zone = 1
#             last_area = area_id
#
#         if ts < start_per_time and ar_id != area_id:
#             if clss == 0:
#                 man_in_zone = 0
#             if clss == 1:
#                 bicycle_in_zone = 0
#             if clss == 16:
#                 dog_in_zone = 0
#             last_area = area_id
#
#         if last_zone!=ar_id:
#             add_all_zones = True
#             try:
#                 all_area[dec_area[str(ar_id)]]+=1
#             except:
#                 pass
#             # if last_zone!=-1:
#             #     try:
#             #         all_area[dec_area[str(last_zone)]] += 1
#             last_zone = ar_id
#
#         if start_per_time <= ts and ts <= end_per_time:
#             if not viz_zone and (man_in_zone or \
#                     ar_id == area_id) and clss == 0:
#                 num_unique_people = 1
#                 viz_zone = True
#
#             #     Он был в этой зоне или он в нее зашел
#             if (man_in_zone or ar_id == area_id) and clss == 0:
#                 if ar_id != area_id:
#                     # print(area_id)
#                     #
#                     # all_area[dec_area[str(area_id)]]+=1
#                     # try:
#                     #     all_area[dec_area[str(ar_id)]]+=1
#                     # except:
#                     #     pass
#                     man_in_zone = 0
#                 elif ar_id == area_id:
#                     # all_area[dec_area[str(area_id)]] += 1
#                     man_in_zone = 1
#                     # add_people_area = True
#
#                 add_people = 1
#                 rep_people += 1
#
#                 flag_add_people = True
#
#             if (bicycle_in_zone or ar_id == area_id) and clss == 1:
#                 if ar_id != area_id:
#                     bicycle_in_zone = 0
#                 elif ar_id == area_id:
#                     bicycle_in_zone = 1
#
#                 add_bicycle = 1
#                 num_bicycle = 1
#
#             if (dog_in_zone or ar_id == area_id) and clss == 16:
#                 if ar_id != area_id:
#                     dog_in_zone = 0
#                 elif ar_id == area_id:
#                     dog_in_zone = 1
#
#                 add_dog = 1
#                 num_dog = 1
#
#     x = []
#     start = start_
#     while start < end_:
#         x.append(datetime.fromtimestamp(start).strftime("%Y-%m-%d %H:%M:%S"))
#         start += per
#
#     # print(f'stat_pople_unique: {[x[0] for x in out_graph_day]}\n'
#     #       f'stat_people_rep {[x[1] for x in out_graph_day]}\n'
#     #       f'x: {x}\n'
#     #       f'stat_type_pos_per: {out_graph_inv}\n')
#     # m = {'С собаками': all_dog,
#     #      'Пешеходы': all_people,
#     #      'Велосипедисты': all_bicycle}
#     # print(f"stat_type_pos_all: {m}")
#     # m = {
#     #     'Мужчины': all_gender[0],
#     #     'Женщины': all_gender[1],
#     #     'Неопределенный тип': all_gender[2],
#     # }
#     # print(f"stat_gender: {m}")
#     # m = {'Дети': all_age[0],
#     #      'Взрослые': all_age[1],
#     #      'Пожилые': all_age[2]}
#     # print(f"stat_age: {m}")
#     # print(f"stat_area: {all_area}")
#     return {
#         'stat_pople_unique':[x[0] for x in out_graph_day],
#         'stat_people_rep':[x[1] for x in out_graph_day],
#         'x': x,
#         'stat_type_pos_per':out_graph_inv,
#         'stat_type_pos_all':{
#                 'С собаками':all_dog,
#                 'Пешеходы':all_people,
#                 'Велосипедисты':all_bicycle,
#                 'Неопределенный тип': 0},
#         'stat_gender':{
#                 'Мужчины':all_gender[0],
#                 'Женщины': all_gender[1],
#                 'Неопределенный тип': all_gender[2],
#         },
#         'stat_age': {
#                 'Дети':all_age[0],
#                 'Взрослые':all_age[1],
#                 'Пожилые':all_age[2]},
#         'stat_area': all_area
#     }

#Статистика для каждой зоны
def statistics_by_zone(start_time, end_time):
    from main import db, PeopleMap, BBoxes
    from sqlalchemy import and_, or_, distinct
    # Получение всех зон
    all_zones = PeopleMap.query.distinct(PeopleMap.area_id).all()
    all_zones = [x.area_id for x in all_zones]

    # Получение статистики для каждой зоны за заданный период
    stat_all_zones = []
    for zone in all_zones:
        res = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_( BBoxes.type == 0, PeopleMap.area_id == zone,
                        between(BBoxes.ts, start_time, end_time)))).count()
        stat_all_zones.append(res)

    return all_zones, stat_all_zones


# Статистика для зоны , разбитая по периодам
def camera_statistics(area_id,start_time, end_time,num_range):
    from main import db, PeopleMap, BBoxes
    from sqlalchemy import and_, or_, distinct

    start_ts_unix = int(time.mktime(start_time.timetuple()))
    cur_ts_unix = start_ts_unix
    end_ts_unix = int(time.mktime(end_time.timetuple()))
    detla_ts_unix = max(1, (end_ts_unix - start_ts_unix) // num_range)

    mass_data = []
    out_graph_day = []

    while cur_ts_unix + detla_ts_unix <= end_ts_unix:
        mass_data.append(datetime.fromtimestamp(cur_ts_unix).strftime("%Y-%m-%d %H:%M:%S"))
        res = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_(BBoxes.type == 0, PeopleMap.area_id == area_id,
                        between(BBoxes.ts, datetime.fromtimestamp(cur_ts_unix),
                                datetime.fromtimestamp(cur_ts_unix + detla_ts_unix))))).count()
        cur_ts_unix += detla_ts_unix
        out_graph_day.append(res)

    return mass_data, out_graph_day


# Статистика по половому признаку
def statistics_by_gender(area_id, start_time, end_time):
    from main import db, PeopleMap, BBoxes
    from sqlalchemy import and_, or_, distinct
    # 0 - Man
    # 1 - Woman
    # 2 - Undefined
    res_man = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.gender == 0,
                        between(BBoxes.ts, start_time,end_time)))).count()

    res_woman = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.gender == 1,
                        between(BBoxes.ts, start_time,end_time)))).count()

    res_undefined = db.session.query(distinct(PeopleMap.person_id)). \
                filter(BBoxes.id == PeopleMap.bbox_id). \
                where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.gender == 2,
                            between(BBoxes.ts, start_time,end_time)))).count()

    return [res_man, res_woman, res_undefined]


# Статистика по возрастному признаку
def age_statistics(area_id, start_time, end_time):
    from main import db, PeopleMap, BBoxes
    from sqlalchemy import and_, or_, distinct
    # 0 - children
    # 1 - adults
    # 2 - elderly

    res_children = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.age == 0,
                        between(BBoxes.ts, start_time,end_time)))).count()

    res_adults = db.session.query(distinct(PeopleMap.person_id)). \
            filter(BBoxes.id == PeopleMap.bbox_id). \
            where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.age == 1,
                        between(BBoxes.ts, start_time,end_time)))).count()

    res_elderly = db.session.query(distinct(PeopleMap.person_id)). \
                filter(BBoxes.id == PeopleMap.bbox_id). \
                where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.age == 2,
                            between(BBoxes.ts, start_time,end_time)))).count()

    return [res_children, res_adults, res_elderly]


def statistics_by_pos(area_id, start_time, end_time):
    from main import db, PeopleMap, BBoxes
    from sqlalchemy import and_, or_, distinct
    # 0 - children
    # 1 - adults
    # 2 - elderly

    res_pedestrians = db.session.query(distinct(PeopleMap.person_id)). \
        filter(BBoxes.id == PeopleMap.bbox_id). \
        where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.type == 0,
                    between(BBoxes.ts, start_time, end_time)))).count()

    res_cyclists = db.session.query(distinct(PeopleMap.person_id)). \
        filter(BBoxes.id == PeopleMap.bbox_id). \
        where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.type == 1,
                    between(BBoxes.ts, start_time, end_time)))).count()

    res_dogs = db.session.query(distinct(PeopleMap.person_id)). \
        filter(BBoxes.id == PeopleMap.bbox_id). \
        where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.type == 2,
                    between(BBoxes.ts, start_time, end_time)))).count()

    res_undefined = db.session.query(distinct(PeopleMap.person_id)). \
        filter(BBoxes.id == PeopleMap.bbox_id). \
        where((and_(PeopleMap.area_id == area_id, BBoxes.type == 0, BBoxes.type == 3,
                    between(BBoxes.ts, start_time, end_time)))).count()

    return [res_pedestrians, res_cyclists, res_dogs, res_undefined]


def statistics(area_id, start_time, end_time, num_range=6):
    # Статистика для камеры, разбитая по периодам
    mass_data, out_graph_day = camera_statistics(area_id,start_time, end_time, num_range)

    # Получение статистики всех зон
    all_zones, stat_all_zones = statistics_by_zone(start_time, end_time)
    all_zones = [str(x) for x in all_zones]


    # Статистика по половому признаку
    all_gender = statistics_by_gender(area_id , start_time, end_time)

    # Статистика по возрастному признаку
    all_age = age_statistics(area_id, start_time, end_time)

    # Статистика по типам посетителей
    res_pedestrians, res_cyclists, res_dogs, res_undefined = statistics_by_pos(area_id, start_time, end_time)

    #  Нижняя центральная Перевести время, разить на интервалы, сделать запросы по всем интервалам
    #  Отобрать уникальные People_map.person_id и среди них по возрасту и полу
    #  Отобрать собака, как?
    # res = db.session.query(distinct(PeopleMap.person_id), PeopleMap.area_id, BBoxes.ts, BBoxes.type, BBoxes.gender, BBoxes.age). \
    #     filter(BBoxes.id == PeopleMap.bbox_id).\
    #     where((and_(BBoxes.cam_id == cam_id, between(BBoxes.ts, start_time, end_time)))).all()

    # res = db.session.query(PeopleMap.person_id, PeopleMap.area_id, BBoxes.ts, BBoxes.type, BBoxes.gender, BBoxes.age). \
    #     filter(BBoxes.id == PeopleMap.bbox_id).\
    #     where((and_(BBoxes.cam_id == cam_id, between(BBoxes.ts, start_time, end_time)))).order_by(PeopleMap.id).all()
    #
    # for people_id, ar_id, ts, clss, gender, age in res:
    #     print(8)
    # k = 2
    # out_graph_inv = [[0 for col in range(2)] for row in range(num_range)]
    # all_area = [0] * len(mas_area)
    # all_gender = [0] * 3
    # all_age = [0] * 4
    # # Подсчет типов посетителей
    # all_dog = 0
    # all_bicycle = 0
    # all_people = 0
    # add_bicycle = 0
    # add_dog = 0
    # add_people = 0
    # x = []
    # start_ = datetime.strptime(str(start_time).split('.')[0], "%Y-%m-%d %H:%M:%S").timestamp()
    # end_ = datetime.strptime(str(end_time).split('.')[0], "%Y-%m-%d %H:%M:%S").timestamp()
    # # end_ = end_time.timestamp()
    # per = max(1,(end_ - start_) // num_range)  #
    # start = start_
    # while start < end_:
    #     x.append(datetime.fromtimestamp(start).strftime("%Y-%m-%d %H:%M:%S"))
    #     start += per
    return {
        # 'stat_pople_unique': out_graph_day,
        'stat_people_rep': out_graph_day,
        'x': mass_data,
        # 'stat_type_pos_per': out_graph_inv,

        'stat_type_pos_all': {
            'С собаками': res_dogs,
            'Пешеходы': res_pedestrians,
            'Велосипедисты': res_cyclists,
            'Неопределенный тип': res_undefined},

        'stat_gender': {
            'Мужчины': all_gender[0],
            'Женщины': all_gender[1],
            'Неопределенный тип': all_gender[2],
        },

        'stat_age': {
            'Дети': all_age[0],
            'Взрослые': all_age[1],
            'Пожилые': all_age[2]},
        'stat_area': stat_all_zones,
        'zones': all_zones
    }


if __name__=="__main__":
    pass