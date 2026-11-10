#!/usr/bin/env python3
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1]
(r/'build').mkdir(exist_ok=True)
subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-Iinclude','scripts/simulation/rover_sim.cpp','-o','build/rover-sim'],cwd=r,check=True)
subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-Icamera/include','camera/test/policy_test.cpp','-o','build/camera-policy-test'],cwd=r,check=True)
subprocess.run([r/'build/camera-policy-test'],check=True)

subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-DCAMERA_BOARD_AI_THINKER','-Icamera/test/stubs','-Icamera/include','camera/test/http_test.cpp','-o','build/camera-http-test'],cwd=r,check=True)
subprocess.run([r/'build/camera-http-test'],check=True)
