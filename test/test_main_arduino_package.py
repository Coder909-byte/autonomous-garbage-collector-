from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from package_main_arduino import package, MODES


class MainArduinoPackage(unittest.TestCase):
    def test_only_explicit_main_sources_are_packaged_for_each_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'firmware').mkdir(); (root/'include').mkdir()
            (root/'firmware/rover.ino').write_text('void setup() {}\nvoid loop() {}\n')
            headers = ('rover_commissioning.h', 'rover_mode.h', 'rover_control.h', 'rover_pins.h', 'rover_telemetry.h')
            for name in headers:
                (root/'include'/name).write_text('// '+name+'\n')
            (root/'include/secrets.h').write_text('PRIVATE_CANARY_DO_NOT_PACKAGE')
            (root/'firmware/old.bin').write_bytes(b'OLD_BINARY')
            with patch('package_main_arduino.ROOT', root):
                for mode in MODES:
                    with self.subTest(mode=mode):
                        sketch, archive = package(mode, root/'output'/mode)
                        with zipfile.ZipFile(archive) as z:
                            expected = {'rover_main/'+n for n in (*headers, 'rover_main.ino', 'rover_build_config.h')}
                            self.assertEqual(set(z.namelist()), expected)
                            self.assertIsNone(z.testzip())
                            for name in expected:
                                self.assertEqual(z.read(name), (sketch.parent/name).read_bytes())
                                self.assertNotIn(b'PRIVATE_CANARY', z.read(name))
                            self.assertIn(('#define ROVER_OPERATING_MODE '+mode).encode(), z.read('rover_main/rover_build_config.h'))

    def test_invalid_mode_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'invalid'
            with self.assertRaises(ValueError):
                package('BYPASS', target)
            self.assertFalse(target.exists())
