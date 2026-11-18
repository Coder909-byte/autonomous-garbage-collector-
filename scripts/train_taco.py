#!/usr/bin/env python3
"""Train the rover's litter detector on TACO (Trash Annotations in Context).

Downloads the 1500 TACO images (640 px thumbnails) and annotations, converts
all 60 TACO categories into a single YOLO class, "litter", and fine-tunes
COCO-pretrained YOLOv8n. Camera seek only needs "is this garbage, and where",
and one class learns far better than 60 from 1500 photos.

    pip install -r vision/requirements-yolo.txt
    python scripts/train_taco.py                      # download, convert, train
    python scripts/train_taco.py --epochs 0           # download and convert only

The result is copied to vision/models/taco_litter.pt, which rover_vision.py
uses automatically. TACO is CC BY 4.0: Proença and Simões, "TACO: Trash
Annotations in Context for Litter Detection", arXiv:2003.06975 (2020).
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TACO_COMMIT = '70479ad9adc3da971a8ae75ac97eb1026910eec7'
ANNOTATIONS_URL = f'https://raw.githubusercontent.com/pedropro/TACO/{TACO_COMMIT}/data/annotations.json'
CLASS_NAME = 'litter'
VAL_PERCENT = 15
MAX_SIDE = 640
# The TACO image host rejects urllib's default user agent.
HEADERS = {'User-Agent': 'Mozilla/5.0 (rover-taco-trainer)'}


def download(url, attempts=4):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as response:
                return response.read()
        except OSError:
            time.sleep(2 ** attempt)
    return None


def fetch(url, path):
    if path.exists() and path.stat().st_size > 0:
        return True
    data = download(url)
    if data is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix('.part').write_bytes(data)
    path.with_suffix('.part').replace(path)
    return True


def fetch_image(image, path):
    """Download, apply EXIF orientation, check it matches the annotation frame, shrink, save without EXIF."""
    if path.exists() and path.stat().st_size > 0:
        return True
    import cv2
    import numpy as np
    data = download(image.get('flickr_640_url') or image['flickr_url'])
    if data is None:
        return False
    # IMREAD_COLOR honours EXIF orientation; TACO annotations are drawn on the oriented image.
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return False
    height, width = frame.shape[:2]
    if abs(width / height - image['width'] / image['height']) > 0.02:
        return False
    scale = MAX_SIDE / max(width, height)
    if scale < 1:
        frame = cv2.resize(frame, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92]))


def is_val(image):
    digest = hashlib.sha1(image['file_name'].encode()).digest()
    return digest[0] * 100 // 256 < VAL_PERCENT


def yolo_lines(boxes, width, height):
    lines = []
    for x, y, w, h in boxes:
        x1, y1 = max(0.0, x), max(0.0, y)
        x2, y2 = min(float(width), x + w), min(float(height), y + h)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        lines.append('0 %.6f %.6f %.6f %.6f' % ((x1 + x2) / 2 / width, (y1 + y2) / 2 / height,
                                                (x2 - x1) / width, (y2 - y1) / height))
    return lines


def prepare(data_dir):
    annotations = data_dir / 'annotations.json'
    if not fetch(ANNOTATIONS_URL, annotations):
        raise SystemExit('Could not download TACO annotations from ' + ANNOTATIONS_URL)
    taco = json.loads(annotations.read_text())
    boxes = {}
    for annotation in taco['annotations']:
        boxes.setdefault(annotation['image_id'], []).append(annotation['bbox'])

    jobs = []
    for image in taco['images']:
        split = 'val' if is_val(image) else 'train'
        stem = image['file_name'].replace('/', '_').rsplit('.', 1)[0]
        jobs.append((image, split, data_dir / 'images' / split / (stem + '.jpg')))
    with ThreadPoolExecutor(16) as pool:
        ok = list(pool.map(lambda job: fetch_image(job[0], job[2]), jobs))
    missing = ok.count(False)
    if missing:
        print('Warning: %d images failed to download or did not match their annotations; skipped' % missing)

    counts = {'train': 0, 'val': 0}
    for (image, split, path), downloaded in zip(jobs, ok):
        if not downloaded:
            continue
        label = data_dir / 'labels' / split / (path.stem + '.txt')
        label.parent.mkdir(parents=True, exist_ok=True)
        # Boxes are in the original image's pixels; normalizing makes them valid for the thumbnail.
        label.write_text('\n'.join(yolo_lines(boxes.get(image['id'], []), image['width'], image['height'])) + '\n')
        counts[split] += 1
    config = data_dir / 'taco_litter.yaml'
    config.write_text(f'path: {data_dir.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: {CLASS_NAME}\n')
    print('TACO ready: %d train, %d val images -> %s' % (counts['train'], counts['val'], config))
    return config


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'build' / 'taco')
    parser.add_argument('--model', default='yolov8n.pt', help='Starting weights')
    parser.add_argument('--epochs', type=int, default=60)
    parser.add_argument('--imgsz', type=int, default=320, help='Match rover_vision.py inference size')
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--device', default=None, help='cpu, 0 (first GPU), ... Default: automatic')
    parser.add_argument('--out', type=Path, default=ROOT / 'vision' / 'models' / 'taco_litter.pt')
    args = parser.parse_args(argv)

    config = prepare(args.data_dir)
    if args.epochs <= 0:
        return 0
    from ultralytics import YOLO
    model = YOLO(args.model)
    model.train(data=str(config), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=args.device,
                project=str(args.data_dir / 'runs'), name='taco_litter', exist_ok=True, patience=20,
                fliplr=0.5, flipud=0.0, degrees=10.0, seed=0, plots=True)
    best = Path(model.trainer.best)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(best, args.out)
    metrics = YOLO(str(args.out)).val(data=str(config), imgsz=args.imgsz, device=args.device, plots=False)
    print('Saved %s  mAP50=%.3f  mAP50-95=%.3f  precision=%.3f  recall=%.3f' % (
        args.out, metrics.box.map50, metrics.box.map, metrics.box.mp, metrics.box.mr))
    return 0


if __name__ == '__main__':
    sys.exit(main())
