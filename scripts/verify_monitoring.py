#!/usr/bin/env python3
"""Software-only monitoring regression; preserve earlier commissioning evidence.

No physical serial opens, firmware uploads or hardware control. Requires installed
project dependencies and Google Chrome (or CHROME_PATH). Logs go in a new folder.
"""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = root / 'artifacts' / 'monitoring-validation' / stamp
out.mkdir(parents=True, exist_ok=True)
python = str(root / '.venv/bin/python')
pio = str(root / '.venv/bin/pio')
protected = ['firmware/rover.ino', 'include/rover_pins.h', 'include/rover_control.h',
             'include/rover_telemetry.h', 'platformio.ini', 'camera/src/main.cpp',
             'camera/platformio.ini', 'camera/include/board_ai_thinker.h']
hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in protected}
commands = [
    ('source-contracts', [python, 'scripts/check_project.py']),
    ('electrical-contracts', [python, 'scripts/check_electrical.py']),
    ('native-tests', [pio, 'test', '-e', 'native']),
    ('python-tests', [python, '-m', 'unittest', 'discover', '-s', 'test', '-p', 'test_*.py', '-v']),
    ('design-exports', [python, 'scripts/check_design_exports.py']),
    ('completion', [python, 'scripts/check_completion.py']),
    ('main-builds', [pio, 'run', '-e', 'esp32dev', '-e', 'wokwi_compile']),
    ('camera-build', [pio, 'run', '-d', 'camera']),
    ('system-graph', [python, 'scripts/check_system.py']),
    # Call the checker directly to avoid replacing earlier handover evidence.
    ('frozen-handover', [python, '-c', "import json,sys; sys.path.insert(0,'scripts'); from check_team_handover import check; print(json.dumps(check(), indent=2))"]),
    ('simulator-camera-host', ['npm', 'run', 'sim:build']),
    ('typescript-tests', ['npm', 'test']),
    ('laptop-build', ['npm', 'run', 'build']),
    ('production-smoke', ['node', 'scripts/smoke_production.mjs']),
    ('browser-tests', ['npm', 'run', 'test:e2e', '--', '--output=' + str(out / 'browser-results')]),
]
wokwi = shutil.which('wokwi-cli') or (str(root / '.tools/wokwi-cli') if (root / '.tools/wokwi-cli').exists() else None)
if wokwi:
    commands.insert(8, ('wokwi-lint', [wokwi, 'lint', 'wokwi']))
results = []
for name, args in commands:
    print('Running ' + name, flush=True)
    with (out / (name + '.log')).open('w') as log:
        result = subprocess.run(args, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    results.append({'name': name, 'exit_code': result.returncode, 'command': args})
    print(name + (': PASS' if result.returncode == 0 else ': FAILED — see log'), flush=True)
unchanged = hashes == {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in protected}
summary = {'utc': stamp, 'hardware_used': False, 'firmware_uploaded': False,
           'physical_validation': 'NOT PERFORMED', 'protected_sources_unchanged': unchanged,
           'protected_sha256': hashes, 'checks': results}
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print('Evidence: ' + str(out), flush=True)
sys.exit(1 if not unchanged or any(r['exit_code'] for r in results) else 0)
