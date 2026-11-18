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

    def test_bench_release_package_is_separate_and_motor_operation_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            sketch, archive = package('MOTOR_OPERATION', target/'bench', bench_release=True)
            self.assertEqual(archive.name, 'rover_main_motor_operation_bench_release.zip')
            with zipfile.ZipFile(archive) as z:
                config = z.read('rover_main/rover_build_config.h')
            self.assertIn(b'#define ROVER_OPERATING_MODE MOTOR_OPERATION', config)
            self.assertIn(b'#define ROVER_BENCH_RELEASE', config)
            self.assertIn(b'#define ROVER_BENCH_RECORD "', config)
            _, locked = package('MOTOR_OPERATION', target/'locked')
            with zipfile.ZipFile(locked) as z:
                self.assertNotIn(b'ROVER_BENCH_RELEASE', z.read('rover_main/rover_build_config.h'))
            for mode in ('PROTECTED_ROVER', 'USB_BENCH_DIAGNOSTIC'):
                with self.assertRaises(ValueError):
                    package(mode, target/mode, bench_release=True)

    def test_wifi_package_adds_only_the_wifi_header_and_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            sketch, archive = package('MOTOR_OPERATION', target/'wifi', bench_release=True, wifi=True)
            self.assertEqual(archive.name, 'rover_main_motor_operation_bench_release_wifi.zip')
            with zipfile.ZipFile(archive) as z:
                names = set(z.namelist())
                config = z.read('rover_main/rover_build_config.h')
            self.assertIn('rover_main/rover_wifi.h', names)
            self.assertEqual(len(names), 8)
            self.assertIn(b'#define ROVER_WIFI', config)
            self.assertIn(b'#define ROVER_BENCH_RELEASE', config)
            _, usb = package('MOTOR_OPERATION', target/'usb', bench_release=True)
            with zipfile.ZipFile(usb) as z:
                self.assertNotIn('rover_main/rover_wifi.h', z.namelist())
                self.assertNotIn(b'ROVER_WIFI', z.read('rover_main/rover_build_config.h'))

    def test_invalid_mode_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'invalid'
            with self.assertRaises(ValueError):
                package('BYPASS', target)
            self.assertFalse(target.exists())
