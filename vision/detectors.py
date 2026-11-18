"""Garbage detectors returning normalized boxes. OpenCV/NumPy are imported lazily
so the payload helpers stay importable (and testable) without them."""
from dataclasses import dataclass
from pathlib import Path
import re

# COCO classes that are plausibly litter on a floor, used with the stock COCO model.
DEFAULT_YOLO_CLASSES = ('bottle', 'cup', 'wine glass', 'bowl', 'fork', 'knife', 'spoon', 'banana',
                        'apple', 'orange', 'sandwich', 'carrot', 'hot dog', 'pizza', 'donut', 'cake')
# Litter model trained on TACO by scripts/train_taco.py; preferred when present.
TACO_MODEL = Path(__file__).resolve().parent / 'models' / 'taco_litter.pt'
MAX_TARGETS = 6


def default_model():
    return str(TACO_MODEL) if TACO_MODEL.exists() else 'yolov8n.pt'


def class_ids(names, classes):
    """Model class ids to keep. None keeps every class.

    classes=None picks automatically: the COCO litter subset when the model has
    those names, otherwise every class (a litter-only model such as TACO).
    """
    if classes is None:
        ids = [i for i, n in names.items() if n.lower() in DEFAULT_YOLO_CLASSES]
        return ids or None
    if tuple(classes) == ('all',):
        return None
    wanted = {c.strip().lower() for c in classes}
    ids = [i for i, n in names.items() if n.lower() in wanted]
    if not ids:
        raise ValueError('None of the requested classes exist in this model: ' + ', '.join(sorted(wanted)))
    return ids
_LABEL = re.compile(r'[^A-Za-z0-9 ._-]')


@dataclass(frozen=True)
class Target:
    label: str
    conf: float
    cx: float
    cy: float
    w: float
    h: float


def clamp01(value):
    return min(1.0, max(0.0, float(value)))


def normalized(label, conf, x1, y1, x2, y2, width, height):
    """Pixel corners -> clamped normalized centre/size target."""
    x1, x2 = sorted((clamp01(x1 / width), clamp01(x2 / width)))
    y1, y2 = sorted((clamp01(y1 / height), clamp01(y2 / height)))
    clean = _LABEL.sub('', str(label))[:32] or 'object'
    return Target(clean, round(clamp01(conf), 3), round((x1 + x2) / 2, 3), round((y1 + y2) / 2, 3),
                  round(x2 - x1, 3), round(y2 - y1, 3))


def payload(detector, targets):
    """Bridge /api/vision body: largest boxes first, bounded to the bridge limit."""
    ranked = sorted(targets, key=lambda t: t.w * t.h, reverse=True)[:MAX_TARGETS]
    return {'detector': _LABEL.sub('', detector)[:32] or 'detector',
            'targets': [t.__dict__ for t in ranked]}


class BlobDetector:
    """Dependency-light fallback: saturated (colourful) blobs on a plain floor.

    Works for wrappers, cans and bottles on grey/beige floors; white paper on a
    light floor is not detected. Ignores the top of the frame (walls/horizon).
    """
    name = 'blob'

    def __init__(self, min_saturation=90, min_value=50, roi_top=0.35, min_area=0.004, max_area=0.4):
        self.min_saturation, self.min_value = min_saturation, min_value
        self.roi_top, self.min_area, self.max_area = roi_top, min_area, max_area

    def detect(self, frame):
        import cv2
        import numpy as np
        height, width = frame.shape[:2]
        top = int(height * self.roi_top)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, self.min_saturation, self.min_value), (180, 255, 255))
        mask[:top] = 0
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        targets = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = (w * h) / float(width * height)
            if not self.min_area <= area <= self.max_area:
                continue
            fill = cv2.contourArea(contour) / float(w * h)
            targets.append(normalized('litter', 0.4 + 0.5 * fill, x, y, x + w, y + h, width, height))
        return targets


class YoloDetector:
    """Ultralytics YOLO: the TACO litter model when present, else stock yolov8n.pt (COCO).
    Stock weights download on first use, so run once with internet before joining the rover's Wi-Fi."""

    def __init__(self, model=None, classes=None, conf=0.35, imgsz=320):
        from ultralytics import YOLO
        model = model or default_model()
        self.model, self.conf, self.imgsz = YOLO(model), conf, imgsz
        self.ids = class_ids(self.model.names, classes)
        self.name = 'yolo-taco' if 'taco' in Path(model).stem.lower() else 'yolo'

    def detect(self, frame):
        height, width = frame.shape[:2]
        result = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, classes=self.ids, verbose=False)[0]
        targets = []
        for (x1, y1, x2, y2), conf, cls in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(),
                                               result.boxes.cls.tolist()):
            targets.append(normalized(result.names[int(cls)], conf, x1, y1, x2, y2, width, height))
        return targets


def make_detector(kind, model, classes, conf):
    if kind in ('auto', 'yolo'):
        try:
            return YoloDetector(model, classes, conf)
        except ImportError:
            if kind == 'yolo':
                raise SystemExit('YOLO needs: pip install -r vision/requirements-yolo.txt')
            print('ultralytics not installed: using the colour-blob detector (pip install -r vision/requirements-yolo.txt for YOLO)')
    return BlobDetector()
