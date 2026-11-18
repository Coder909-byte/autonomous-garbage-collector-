#!/usr/bin/env python3
"""Package only the main ESP32 sketch/headers. Never reads secrets or uploads."""
from pathlib import Path
import argparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODES = ('PROTECTED_ROVER', 'USB_BENCH_DIAGNOSTIC')

def package(mode, output):
    if mode not in MODES:
        raise ValueError('Unknown operating mode')
    output = Path(output)
    sketch = output / 'rover_main'
    sketch.mkdir(parents=True, exist_ok=True)
    # Explicit inventory prevents accidental inclusion of local configuration.
    files = {'rover_main.ino': '#include "rover_build_config.h"\n' + (ROOT/'firmware/rover.ino').read_text(encoding='utf-8'),
             'rover_build_config.h': '#pragma once\n// Compile-time selection; USB bench never drives motors.\n#define ROVER_OPERATING_MODE ' + mode + '\n'}
    for name in ('rover_mode.h', 'rover_control.h', 'rover_pins.h', 'rover_telemetry.h'):
        files[name] = (ROOT/'include'/name).read_text(encoding='utf-8')
    for name, contents in files.items():
        (sketch/name).write_bytes(contents.encode('utf-8'))
    archive = output / ('rover_main_' + mode.lower() + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, contents in files.items():
            z.writestr('rover_main/' + name, contents)
    return sketch, archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, default='PROTECTED_ROVER')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    target = args.output or ROOT/'build/arduino'/args.mode.lower()
    sketch, archive = package(args.mode, target)
    print('Mode:', args.mode)
    print('Sketch:', sketch)
    print('ZIP:', archive)
