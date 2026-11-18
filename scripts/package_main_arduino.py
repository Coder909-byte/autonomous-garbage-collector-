#!/usr/bin/env python3
"""Package only the main ESP32 sketch/headers. Never reads secrets or uploads."""
from pathlib import Path
import argparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODES = ('PROTECTED_ROVER', 'USB_BENCH_DIAGNOSTIC', 'MOTOR_OPERATION')
BENCH_RECORD = 'SUPERVISED-BENCH-TEST_wheels-off-ground_fused-supply_manual-disconnect'

def package(mode, output, bench_release=False):
    if mode not in MODES:
        raise ValueError('Unknown operating mode')
    if bench_release and mode != 'MOTOR_OPERATION':
        raise ValueError('Bench release applies only to MOTOR_OPERATION')
    output = Path(output)
    sketch = output / 'rover_main'
    sketch.mkdir(parents=True, exist_ok=True)
    # Explicit inventory prevents accidental inclusion of local configuration.
    files = {'rover_main.ino': '#include "rover_build_config.h"\n' + (ROOT/'firmware/rover.ino').read_text(encoding='utf-8'),
             'rover_build_config.h': '#pragma once\n// Compile-time selection; USB bench never drives motors.\n#define ROVER_OPERATING_MODE ' + mode + '\n'}
    if bench_release:
        files['rover_build_config.h'] += ('// Owner-supervised bench release: motor outputs are not commissioning-locked.\n'
                                         '#define ROVER_BENCH_RELEASE\n#define ROVER_BENCH_RECORD "' + BENCH_RECORD + '"\n')
    for name in ('rover_commissioning.h', 'rover_mode.h', 'rover_control.h', 'rover_pins.h', 'rover_telemetry.h'):
        files[name] = (ROOT/'include'/name).read_text(encoding='utf-8')
    for name, contents in files.items():
        (sketch/name).write_bytes(contents.encode('utf-8'))
    archive = output / ('rover_main_' + mode.lower() + ('_bench_release' if bench_release else '') + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, contents in files.items():
            z.writestr('rover_main/' + name, contents)
    return sketch, archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, default='PROTECTED_ROVER')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bench-release', action='store_true',
                        help='MOTOR_OPERATION only: build the supervised bench package without the commissioning lock')
    args = parser.parse_args()
    if args.bench_release and args.mode != 'MOTOR_OPERATION':
        parser.error('--bench-release requires --mode MOTOR_OPERATION')
    target = args.output or ROOT/'build/arduino'/(args.mode.lower() + ('_bench_release' if args.bench_release else ''))
    sketch, archive = package(args.mode, target, args.bench_release)
    print('Mode:', args.mode, '(bench release)' if args.bench_release else '')
    print('Sketch:', sketch)
    print('ZIP:', archive)
