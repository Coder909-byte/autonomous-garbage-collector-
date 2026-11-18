from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CommissioningBuildGuard(unittest.TestCase):
    def preprocess(self, *flags):
        return subprocess.run(['c++', '-x', 'c++', '-E', '-Iinclude', *flags, '-'],
                              input='#include "rover_mode.h"\n', cwd=ROOT,
                              capture_output=True, text=True)

    def test_host_commissioning_fixture_is_forbidden_in_every_hardware_context(self):
        for macro in ('ARDUINO=10819', 'ARDUINO_ARCH_ESP32', 'ESP_PLATFORM'):
            with self.subTest(macro=macro):
                p = self.preprocess('-DROVER_OPERATING_MODE=MOTOR_OPERATION',
                                    '-DROVER_COMMISSIONING_TEST_FIXTURE', '-D'+macro)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('Commissioning test fixture is forbidden', p.stderr)

    def test_all_release_modes_compile_without_test_override(self):
        for mode in ('PROTECTED_ROVER', 'USB_BENCH_DIAGNOSTIC', 'MOTOR_OPERATION'):
            with self.subTest(mode=mode):
                self.assertEqual(self.preprocess('-DROVER_OPERATING_MODE='+mode).returncode, 0)

    def test_unknown_mode_is_a_compile_error(self):
        self.assertNotEqual(self.preprocess('-DROVER_OPERATING_MODE=99').returncode, 0)
