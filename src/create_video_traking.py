import os
import re
import time
import datetime
import magic
import cv2 as cv
from main import db, BBoxes, Camera, PeopleMap

LONG_TIME_STREAM = 1 * 60
classes_age = ['Children', 'Adults', 'Elderly']
classes_gender = ['Female', 'Male']
PATH_VIDEO_SAVE = 'tmp'

def processing_video(cur_path, start_ts_unix,cam_id):
    from main import PeopleMap
    cap = cv.VideoCapture(cur_path)
    fps = 5
    print(f"Video FPS: {fps}")
    count = 0
    writer = cv.VideoWriter(f'{cam_id}_new.avi',
                            cv.VideoWriter_fourcc(*'XVID'),
                            20,(640,640))
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:

            if count % fps == 0:
                frame = cv.resize(frame, (640, 640))
                cur_img_res = dict()
                cur_ts = start_ts_unix + count // fps
                cur_img_res["ts"] = cur_ts
                ts_ = datetime.datetime.fromtimestamp(cur_ts).strftime('%Y-%m-%d %H:%M:%S')
                # res = BBoxes.query.filter_by(cam_id=cam_id, ts=ts_).order_by(BBoxes.id).all()
                res = BBoxes.query.filter_by(cam_id=cam_id, frame_id=count).order_by(BBoxes.id).all()
                print(count)
                for bbox in res:
                    query = PeopleMap.query.filter_by(bbox_id=bbox.id).all()
                    if len(query)==0:
                        continue
                    query_people = query[0]
                    cnt = 15
                    cv.rectangle(frame,(bbox.l,bbox.t),(bbox.r,bbox.b),
                                 ((255+cnt*query_people.person_id)%256,
                                (255+2*cnt*query_people.person_id)%256,
                                (255+7*cnt*query_people.person_id)%256),
                                 thickness=2)


                    classes_age = ['Children', 'Adults', 'Elderly']
                    classes_gender = ['Female', 'Male']
                    cv.putText(img = frame,
                               text = classes_age[bbox.age],
                               org=(bbox.l,bbox.t+50),
                               fontFace=cv.FONT_HERSHEY_PLAIN,
                               fontScale=2,
                               color= ((255+cnt*query_people.person_id)%256,
                                       (255+2*cnt*query_people.person_id)%256,
                                       (255+7*cnt*query_people.person_id)%256),
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
                # cv.imshow('test',frame)
                # cv.waitKey()
                # cv.destroyAllWindows()
                writer.write(frame)

            count+=1
        else:
            break
        if cv.waitKey(20) & 0xFF == ord('q'):
            break
    writer.release()
    cap.release()
    cv.destroyAllWindows()


def create_video(cam_id):
    res = BBoxes.query.filter_by(cam_id=cam_id).order_by(BBoxes.frame_id.desc()).first().frame_id
    FPS = Camera.query.where(Camera.id == cam_id).first()
    start_frame = res - LONG_TIME_STREAM*FPS.fps_video
    cnt_frame = LONG_TIME_STREAM*FPS.fps_video / FPS.fps
    cur_frame = 0
    writer = cv.VideoWriter(os.path.join(PATH_VIDEO_SAVE,f'{cam_id}_create.avi'),
                            cv.VideoWriter_fourcc(*'XVID'),
                            20,(640,640))

    for cur_img in range(start_frame, res):
        if os.path.exists(os.path.join('tmp', cam_id , f'{cur_img}.jpg')):
            frame = cv.imread(os.path.join('tmp', cam_id , f'{cur_img}.jpg'))

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

            cur_frame +=1
            ret_string = "data:" + '{' + f'{0}:{int(cur_frame/cnt_frame)}' + '}' + "\n\n"
            print(ret_string)
            yield ret_string

    ret_string = "data:" + '{' + f'{0}:{100}' + '}' + "\n\n"
    print(ret_string)
    yield ret_string
    writer.release()


if __name__=="__main__":
    create_video(11)
    from main import BBoxes, Polygon
    path = 'D:\Park\park\\data'
    print('Start')
    start_ts_unix = int(time.mktime(datetime.datetime.strptime('2020-01-01 01-01-01', "%Y-%m-%d %H-%M-%S").timetuple()))
    processing_video(os.path.join(path,'demo_input_2.avi'), start_ts_unix, 11)
    # processing_video(os.path.join(path,'demo_karusel.avi'), start_ts_unix, 16)
