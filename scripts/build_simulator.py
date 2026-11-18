#!/usr/bin/env python3
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1]
(r/'build').mkdir(exist_ok=True)
subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-Iinclude','scripts/simulation/rover_sim.cpp','-o','build/rover-sim'],cwd=r,check=True)
subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-DROVER_OPERATING_MODE=USB_BENCH_DIAGNOSTIC','-Itest/stubs','-Iinclude','scripts/simulation/bench_serial.cpp','-o','build/rover-bench-sim'],cwd=r,check=True)
for name,flags in [('motor-pending',[]),('motor-qualified-test',['-DROVER_COMMISSIONING_TEST_FIXTURE']),('motor-bench-release',['-DROVER_BENCH_RELEASE','-DROVER_BENCH_RECORD="SUPERVISED-BENCH-TEST"'])]:
 subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-DROVER_OPERATING_MODE=MOTOR_OPERATION','-Itest/stubs','-Iinclude',*flags,'scripts/simulation/bench_serial.cpp','-o','build/rover-'+name+'-sim'],cwd=r,check=True)
subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-Icamera/include','camera/test/policy_test.cpp','-o','build/camera-policy-test'],cwd=r,check=True)
subprocess.run([r/'build/camera-policy-test'],check=True)

subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-DCAMERA_BOARD_AI_THINKER','-Icamera/test/stubs','-Icamera/include','camera/test/http_test.cpp','-o','build/camera-http-test'],cwd=r,check=True)
subprocess.run([r/'build/camera-http-test'],check=True)
