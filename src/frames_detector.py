import cv2
import numpy as np
# from vgg_19 import VGG_19
# from tensorflow.keras.applications.vgg19 import preprocess_input
# from keras.preprocessing import image
# from IPython.display import display
# from PIL import Image
# import ipywidgets as widgets
# import matplotlib.pyplot as plt
from yolov5.yolo_detector import YoloDetector

import time
import datetime
import os
import json
import random

detector = None

os.environ["CUDA_VISIBLE_DEVICES"]="0"

# model = VGG_19(include_top=False, weights='imagenet')

def yolo_predict(filename):
    global detector
    if detector is None:
        detector = YoloDetector()
    return detector.predict(filename)


def get_features(img):
    img = cv2.resize(img, (200, 200))
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    return json.dumps(model.predict(img).flatten().tolist())

        
def process_file(cur_path, start_ts_unix, cam_id, save_to_db=True):
    cap = cv2.VideoCapture(cur_path)   

    if not cap.isOpened():
        print(f"Error opening file {cur_path}")
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    if int(major_ver)  < 3 :
        fps = int(cap.get(cv2.cv.CV_CAP_PROP_FPS))
    else :
        fps = int(cap.get(cv2.CAP_PROP_FPS))
    fps = 5
    print(f"Video FPS: {fps}")
    count = 0
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            if count % fps == 0:
                cur_img = frame            
                cv2.imwrite(f"tmp/{cam_id}_last.png", cur_img)
                print(f"Saving current frame {count}")
                cur_img_res = dict()
                cur_ts = start_ts_unix + count // fps
                cur_img_res["ts"] = cur_ts
                print(f"Detect boxes")
                cur_img_res["bboxes"] = yolo_predict(f"tmp/{cam_id}_last.png")
                print(cur_img_res["bboxes"])
                # Получение фич для каждого бокса
                # надо выпилить
                # for cur_bbox in cur_img_res["bboxes"]:
                #     cur_bbox["features"] = str(get_features(cur_img[cur_bbox["top"]:cur_bbox["bottom"], cur_bbox["left"]:cur_bbox["right"]]))
#                 print(cur_img_res)
                from main import db, BBoxes
                ts = datetime.datetime.fromtimestamp(cur_img_res["ts"]).strftime("%Y-%m-%d %H:%M:%S")
                for cur_bbox in cur_img_res["bboxes"]:
                    left = cur_bbox["left"]
                    right = cur_bbox["right"]
                    top = cur_bbox["top"]
                    bottom = cur_bbox["bottom"]
                    #features = cur_bbox["features"]
                    tp = cur_bbox["class"]
                    new_bbox = BBoxes(
                        cam_id=cam_id, 
                        l=left, 
                        r=right, 
                        t=top, 
                        b=bottom, 
                        ts=ts, 
                        tp=tp, 
                        gender=random.randint(1, 3), 
                        age=random.randint(1, 4), 
                        frame_id=count,
                        # features=features,
                        features="",
                        direction="")
                    if save_to_db:
                        try:
                            db.session.add(new_bbox)
                            db.session.commit()  
                        except Exception as e:
                            db.session.rollback()
                            print(f"Error processing frame {count} of {cur_path}")
                            print(e)
            count += 1
        else:
            break

    # When everything done, release the video capture object
    cap.release()

    # Closes all the frames
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print(yolo_predict("tmp/cur.png"))
    pass
