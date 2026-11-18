#!/usr/bin/env python3
"""Rover vision service: ESP32-CAM frames -> garbage detections -> local bridge.

The bridge only steers on these detections while the operator has switched
on Camera seek in Mission Control. Stopping this service stops the stream of
detections, and the bridge then holds the rover still.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detectors import DEFAULT_YOLO_CLASSES, make_detector, payload  # noqa: E402


def fetch_jpeg(url, timeout=3.0):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if not str(response.headers.get('Content-Type', '')).startswith('image/jpeg'):
            raise ValueError('camera did not return a JPEG')
        return response.read()


def post_detections(bridge, body, timeout=2.0):
    request = urllib.request.Request(bridge.rstrip('/') + '/api/vision', data=json.dumps(body).encode(), method='POST',
                                     headers={'Content-Type': 'application/json', 'X-Rover-Client': 'vision'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read() or b'{}')


class Frames:
    """Snapshots from the bridge camera proxy (default), the camera itself, or a local video source."""

    def __init__(self, args):
        import cv2
        self.cv2 = cv2
        self.capture = None
        if args.source is not None:
            self.capture = cv2.VideoCapture(int(args.source) if args.source.isdigit() else args.source)
            if not self.capture.isOpened():
                raise SystemExit('Cannot open video source ' + args.source)
        elif args.camera:
            self.url = args.camera.rstrip('/') + '/snapshot'
        else:
            self.url = args.bridge.rstrip('/') + '/api/camera/snapshot'

    def read(self):
        if self.capture is not None:
            ok, frame = self.capture.read()
            if not ok:
                raise ValueError('video source ended')
            return frame
        import numpy as np
        frame = self.cv2.imdecode(np.frombuffer(fetch_jpeg(self.url), np.uint8), self.cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError('JPEG decode failed')
        return frame


def draw(cv2, frame, body, vision):
    height, width = frame.shape[:2]
    for t in body['targets']:
        x1, y1 = int((t['cx'] - t['w'] / 2) * width), int((t['cy'] - t['h'] / 2) * height)
        x2, y2 = int((t['cx'] + t['w'] / 2) * width), int((t['cy'] + t['h'] / 2) * height)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 220, 120), 2)
        cv2.putText(frame, '%s %d%%' % (t['label'], t['conf'] * 100), (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 220, 120), 1)
    status = 'SEEK %s' % vision.get('phase', '?') if vision.get('enabled') else 'Camera seek off'
    cv2.putText(frame, status, (6, height - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 80), 1)
    cv2.imshow('Rover vision', frame)
    return cv2.waitKey(1) & 0xFF != ord('q')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bridge', default='http://127.0.0.1:8787', help='Mission Control bridge URL')
    parser.add_argument('--camera', help='Read snapshots directly from the ESP32-CAM, e.g. http://192.168.4.2')
    parser.add_argument('--source', help='Local test source instead of the ESP32-CAM: webcam index or video file')
    parser.add_argument('--detector', choices=('auto', 'yolo', 'blob'), default='auto')
    parser.add_argument('--model', help='YOLO weights. Default: vision/models/taco_litter.pt if present, else yolov8n.pt (COCO)')
    parser.add_argument('--classes', help='Comma-separated YOLO class names, or "all". Default: every class of a '
                        'litter model; with COCO weights: ' + ', '.join(DEFAULT_YOLO_CLASSES))
    parser.add_argument('--conf', type=float, default=0.35)
    parser.add_argument('--fps', type=float, default=5.0)
    parser.add_argument('--show', action='store_true', help='Show a preview window with boxes (q to quit)')
    args = parser.parse_args(argv)
    classes = tuple(c.strip() for c in (args.classes or '').split(',') if c.strip()) or None
    detector = make_detector(args.detector, args.model, classes, args.conf)
    frames = Frames(args)
    print('Vision: detector=%s -> %s/api/vision at up to %.1f fps. Ctrl+C stops.' % (detector.name, args.bridge, args.fps), flush=True)
    period, last_error, warned_at = 1.0 / max(0.5, args.fps), None, 0.0
    while True:
        started = time.monotonic()
        try:
            frame = frames.read()
            body = payload(detector.name, detector.detect(frame))
            vision = post_detections(args.bridge, body).get('vision') or {}
            if last_error:
                print('Vision: recovered', flush=True)
                last_error = None
            if args.show and not draw(frames.cv2, frame, body, vision):
                return 0
        except KeyboardInterrupt:
            return 0
        except (urllib.error.URLError, OSError, ValueError) as error:
            message = getattr(error, 'reason', None) or str(error)
            if str(message) != last_error or time.monotonic() - warned_at > 10:
                print('Vision: waiting (%s). Is the bridge running and the camera connected in Mission Control?' % message, flush=True)
                last_error, warned_at = str(message), time.monotonic()
            time.sleep(1.0)
            continue
        time.sleep(max(0.0, period - (time.monotonic() - started)))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
