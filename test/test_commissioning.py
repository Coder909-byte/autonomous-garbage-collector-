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

    def check(self, *flags):
        return subprocess.run(['c++', '-std=c++11', '-x', 'c++', '-fsyntax-only', '-Iinclude', *flags, '-'],
                              input='#include "rover_mode.h"\nstatic_assert(rover::MOTOR_OUTPUTS_ALLOWED, "locked");\n',
                              cwd=ROOT, capture_output=True, text=True)

    def test_default_motor_operation_stays_locked(self):
        p = self.check('-DROVER_OPERATING_MODE=MOTOR_OPERATION', '-DARDUINO=10819')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('locked', p.stderr)

    def test_bench_release_unlocks_hardware_build_with_record(self):
        p = self.check('-DROVER_OPERATING_MODE=MOTOR_OPERATION', '-DARDUINO=10819',
                       '-DROVER_BENCH_RELEASE', '-DROVER_BENCH_RECORD="BENCH"')
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_bench_release_requires_nonempty_record(self):
        missing = self.check('-DROVER_OPERATING_MODE=MOTOR_OPERATION', '-DROVER_BENCH_RELEASE')
        self.assertIn('requires ROVER_BENCH_RECORD', missing.stderr)
        empty = self.check('-DROVER_OPERATING_MODE=MOTOR_OPERATION', '-DROVER_BENCH_RELEASE', '-DROVER_BENCH_RECORD=""')
        self.assertIn('must not be empty', empty.stderr)

    def test_unknown_mode_is_a_compile_error(self):
        self.assertNotEqual(self.preprocess('-DROVER_OPERATING_MODE=99').returncode, 0)
