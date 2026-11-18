import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vision'))
from detectors import MAX_TARGETS, BlobDetector, class_ids, normalized, payload  # noqa: E402

HAS_CV = importlib.util.find_spec('cv2') is not None and importlib.util.find_spec('numpy') is not None


class VisionPayload(unittest.TestCase):
    def test_boxes_are_clamped_normalized_and_label_sanitized(self):
        t = normalized('bot<tle>', 1.7, -20, 50, 160, 300, 320, 240)
        self.assertEqual(t.label, 'bottle')
        self.assertEqual((t.conf, t.cx, t.w, t.h), (1.0, 0.25, 0.5, 0.792))
        self.assertTrue(all(0 <= v <= 1 for v in (t.cx, t.cy, t.w, t.h)))

    def test_payload_is_bounded_largest_first_and_fits_the_bridge_body_limit(self):
        targets = [normalized('cup', 0.9, 0, 0, 10 * (i + 1), 10 * (i + 1), 320, 240) for i in range(10)]
        body = payload('yolo', targets)
        self.assertEqual(len(body['targets']), MAX_TARGETS)
        sizes = [t['w'] * t['h'] for t in body['targets']]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertLess(len(json.dumps(body)), 1024)


class ClassSelection(unittest.TestCase):
    COCO = {0: 'person', 39: 'bottle', 41: 'cup', 56: 'chair'}

    def test_automatic_selection_keeps_coco_litter_only(self):
        self.assertEqual(class_ids(self.COCO, None), [39, 41])

    def test_automatic_selection_keeps_every_class_of_a_litter_model(self):
        self.assertIsNone(class_ids({0: 'litter'}, None))

    def test_explicit_and_all_selections(self):
        self.assertEqual(class_ids(self.COCO, ('Cup',)), [41])
        self.assertIsNone(class_ids(self.COCO, ('all',)))
        with self.assertRaises(ValueError):
            class_ids({0: 'litter'}, ('bottle',))


@unittest.skipUnless(HAS_CV, 'opencv-python and numpy not installed (pip install -r vision/requirements.txt)')
class BlobDetection(unittest.TestCase):
    def test_colourful_item_on_grey_floor_is_found_and_walls_ignored(self):
        import numpy as np
        frame = np.full((240, 320, 3), 128, np.uint8)
        frame[150:200, 40:90] = (0, 0, 255)      # red wrapper on the floor, left side
        frame[10:50, 200:260] = (255, 0, 0)      # blue poster above the floor line
        targets = BlobDetector().detect(frame)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].label, 'litter')
        self.assertAlmostEqual(targets[0].cx, 65 / 320, places=2)

    def test_plain_floor_has_no_targets(self):
        import numpy as np
        self.assertEqual(BlobDetector().detect(np.full((240, 320, 3), 128, np.uint8)), [])


if __name__ == '__main__':
    unittest.main()
