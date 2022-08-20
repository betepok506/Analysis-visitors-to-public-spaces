import argparse
import asyncio
import os
import sys
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
# FILE = Path(__file__).absolute()
# sys.path.append(FILE.parents[0].as_posix())



from models.common import DetectMultiBackend
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.torch_utils import select_device, time_sync

detector = None


class YoloDetector:
    def __init__(self):
        print(os.getcwd())
        self.weights = 'yolov5x.pt'  # model.pt path(s)
        self.source = './src/yolov5/data/images'  # file/dir/URL/glob, 0 for webcam
        self.data = './src/yolov5/data/coco128.yaml'  # dataset.yaml path
        self.imgsz = (640, 640)  # inference size (height, width)
        self.conf_thres = 0.25  # confidence threshold
        self.iou_thres = 0.45  # NMS IOU threshold
        self.max_det = 1000  # maximum detections per image
        # self.device = 'cpu'  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        self.device = torch.device(0 if torch.cuda.is_available() else "cpu")  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        self.view_img = False  # show results
        self.save_txt = False  # save results to *.txt
        self.save_conf = False  # save confidences in --save-txt labels
        self.save_crop = False  # save cropped prediction boxes
        self.nosave = False  # do not save images/videos
        self.classes = [0, 1, 16]  # filter by class: --class 0, or --class 0 2 3
        self.agnostic_nms = False  # class-agnostic NMS
        self.augment = False  # augmented inference
        self.visualize = False  # visualize features
        self.update = False  # update all models
        self.project = 'runs/detect'  # save results to project/name
        self.name = 'exp'  # save results to project/name
        self.exist_ok = False  # existing project/name ok, do not increment
        self.line_thickness = 3  # bounding box thickness (pixels)
        self.hide_labels = False  # hide labels
        self.hide_conf = False  # hide confidences
        self.half = False  # use FP16 half-precision inference
        self.dnn = False  # use OpenCV DNN for ONNX inference

        self.save_img = not self.nosave and not self.source.endswith('.txt')
        self.save_dir = increment_path(Path(self.project) / self.name, exist_ok=self.exist_ok)  # increment run
        (self.save_dir / 'labels' if self.save_txt else self.save_dir).mkdir(parents=True, exist_ok=True)  # make dir
        # Load model
        self.device = select_device(self.device) ##&&
        self.model = DetectMultiBackend(self.weights, device=self.device, dnn=self.dnn, data=self.data)
        self.stride, self.names, self.pt, self.jit, self.onnx, self.engine = self.model.stride, self.model.names, self.model.pt, self.model.jit, self.model.onnx, self.model.engine
        self.imgsz = check_img_size(self.imgsz, s=self.stride)  # check image size

        # Half
        self.half &= (self.pt or self.jit or self.onnx or self.engine) and self.device.type != 'cpu'  # FP16 supported on limited backends with CUDA
        if self.pt or self.jit:
            self.model.model.half() if self.half else self.model.model.float()

    def predict(self, img):
        res_dict = []
        dataset = LoadImages(img, img_size=self.imgsz, stride=self.stride, auto=self.pt)
        bs = 1  # batch_size

        self.model.warmup(imgsz=(1 if self.pt else bs, 3, *self.imgsz), half=self.half)  # warmup

        for path, im, im0s, vid_cap, s in dataset:

            im = torch.from_numpy(im).to(self.device)
            im = im.half() if self.half else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

            # Inference
            pred = self.model(im, augment=self.augment, visualize=self.visualize)

            # NMS
            pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, self.classes, self.agnostic_nms, max_det=self.max_det)

            for i, det in enumerate(pred):  # per image
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()
                    for *xyxy, conf, cls in reversed(det):
                        x = torch.tensor(xyxy).view(1, 4)
                        l = int(x[:, 0])
                        t = int(x[:, 1])
                        r = int(x[:, 2])
                        b = int(x[:, 3])

                        res_dict.append({
                            "left": l,
                            "right": r,
                            "top": t,
                            "bottom": b,
                            "confidence": float(conf),
                            "class": int(cls)
                        })
        return res_dict


#
# def yolo_predict(filename):
#     global detector
#     if detector is None:
#         detector = YoloDetector()
#     return detector.predict(filename)
#
#
# if __name__=="__main__":
#     print(yolo_predict('../../tmp/3_last.png'))