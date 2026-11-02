#!/usr/bin/env python3
"""Run unpowered software verification sequentially. Never uploads firmware."""
from pathlib import Path
import shutil
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
pio = root / '.venv/bin/pio'
if not pio.exists():
    sys.exit('Create .venv and install requirements-dev.txt first (see README.md)')
artifacts = root / 'artifacts'
artifacts.mkdir(exist_ok=True)
def run(args, log):
    print('Running: ' + ' '.join(map(str,args)), flush=True)
    with (artifacts/log).open('w') as out:
        result = subprocess.run(list(map(str,args)), cwd=root, stdout=out, stderr=subprocess.STDOUT)
    print((artifacts/log).read_text(), end='')
    if result.returncode:
        sys.exit(result.returncode)
run([sys.executable,root/'scripts/check_project.py'],'static-checks.log')
run([sys.executable,root/'scripts/check_electrical.py'],'electrical-checks.log')
# PlatformIO can invalidate build directories between test/build actions.
# Keep every invocation sequential; finish with deployable build artifacts.
run([pio,'test','-e','native'],'native-tests.log')
run([sys.executable,'-m','unittest','discover','-s','test','-p','test_*.py','-v'],'python-tests.log')
run([pio,'run','-e','esp32dev','-e','wokwi_compile'],'build.log')
wokwi = shutil.which('wokwi-cli')
if not wokwi and (root/'.tools/wokwi-cli').exists():
    wokwi = str(root/'.tools/wokwi-cli')
if wokwi:
    run([wokwi,'lint','wokwi'],'wokwi-lint.log')
else:
    print('SKIP Wokwi CLI lint: executable is not installed')
print('Software checks passed. Wokwi runtime and physical hardware are not verified by this script.')
