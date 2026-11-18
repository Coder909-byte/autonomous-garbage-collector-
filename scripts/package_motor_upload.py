#!/usr/bin/env python3
"""Export compiled main-ESP32 images and matching Arduino sources. Never upload."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from package_main_arduino import BENCH_RECORD, ROOT, package


def commissioning_ready(bench_release=False):
    # Evaluate the actual header; do not infer readiness from the six flags or
    # let a command-line option substitute for the release record.
    with tempfile.TemporaryDirectory() as directory:
        executable = Path(directory) / 'readiness'
        subprocess.run(['c++', '-std=c++11', '-x', 'c++', '-I'+str(ROOT/'include'),
                        '-DROVER_OPERATING_MODE=MOTOR_OPERATION',
                        *(['-DROVER_BENCH_RELEASE', '-DROVER_BENCH_RECORD="'+BENCH_RECORD+'"'] if bench_release else []),
                        '-', '-o', str(executable)],
                       input='#include "rover_mode.h"\nint main(){return rover::COMMISSIONING_READY?0:1;}\n',
                       text=True, check=True)
        result = subprocess.run([str(executable)], check=False)
        if result.returncode not in (0, 1):
            raise RuntimeError('Could not evaluate commissioning record')
        return result.returncode == 0


def export(build, boot_app, output, bench_release=False):
    build, boot_app, output = Path(build), Path(boot_app), Path(output)
    inputs = {'bootloader.bin': build/'bootloader.bin', 'partitions.bin': build/'partitions.bin',
              'boot_app0.bin': boot_app, 'firmware.bin': build/'firmware.bin'}
    # Validate before replacing any existing archive.
    images = {name: path.read_bytes() for name, path in inputs.items()}
    if any(not value for value in images.values()):
        raise ValueError('Empty firmware image')
    ready = commissioning_ready(bench_release)
    sketch, archive = package('MOTOR_OPERATION', output, bench_release)
    files = {'rover_main/'+path.name: path.read_bytes() for path in sketch.iterdir()
             if path.name in ('rover_main.ino', 'rover_build_config.h', 'rover_commissioning.h',
                              'rover_mode.h', 'rover_control.h', 'rover_pins.h', 'rover_telemetry.h')}
    files.update({'firmware/'+name: data for name, data in images.items()})
    status = ('SUPERVISED BENCH RELEASE: motor outputs are not commissioning-locked. Wheels off the ground, fused supply, manual disconnect within reach.'
              if bench_release else
              'Compile-time commissioning record accepted; hardware behavior is not detected or verified by this package.'
              if ready else 'OUTPUTS INHIBITED: commissioning flags and a nonempty retained record identifier are required. ARM remains rejected.')
    instructions = f'''MAIN ESP32 ONLY - MOTOR_OPERATION - Arduino-ESP32 2.0.17
{status}

Compiled target: ESP32 Dev Module, 240 MHz CPU, DIO/40 MHz, 4 MB flash,
default partitions, PSRAM disabled. GPIO assignments are unchanged.
ESP32-CAM firmware and credentials are not included.

DELL G15 / POWERSHELL
1. Disconnect motor power for flashing. Stop Mission Control (Ctrl+C) and close
   Serial Monitor. Connect the MAIN ESP32 USB; verify it is COM7.
2. Extract the ZIP into its own folder. Open PowerShell in that folder.
3. Install the pinned flashing tool (requires Python 3):
   py -3 -m pip install esptool==4.9.0
4. Verify extracted payload hashes:
   $m = Get-Content .\\manifest.json -Raw | ConvertFrom-Json
   foreach ($p in $m.sha256.PSObject.Properties) {{ if ((Get-FileHash -Algorithm SHA256 -LiteralPath $p.Name).Hash.ToLowerInvariant() -ne $p.Value) {{ throw "Hash mismatch: $($p.Name)" }} }}
5. Flash the already-compiled main images at 115200 baud (one line):
   py -3 -m esptool --chip esp32 --port COM7 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 4MB 0x1000 firmware/bootloader.bin 0x8000 firmware/partitions.bin 0xe000 firmware/boot_app0.bin 0x10000 firmware/firmware.bin
   If connection stalls at Connecting, hold BOOT until writing starts.
6. Inspect serial at 115200 baud, newline: READY MOTOR_OPERATION DISARMED and
   TEL protocol v1. Boot must be armed:false, en:false and applied:0.
   Expected compile-time commissioningReady: {str(ready).lower()}.
   Runtime PWM_FAULT or COMMAND_TIMEOUT can still inhibit a released build.
7. Close Serial Monitor. In the updated project run npm run build, then npm start.
   Open http://127.0.0.1:8787, Ctrl+F5, select Main ESP32 USB serial, COM7,
   Connect rover. Wait for Protocol ready. ARM requires commissioningReady:true,
   inhibit:NONE and clear software E-stop. ARM alone does not start movement.
   After the physical first-test procedure permits motor power, explicitly ARM,
   wait for enabled directions, hold W/S/A/D and release to stop.
   S/Space stops without latching; STOP/ESTOP latch; DISARM disables outputs.
   Loss of accepted commands for 1200 ms disarms. No automatic rearm occurs.

ARDUINO IDE SOURCE ALTERNATIVE
Open rover_main/rover_main.ino using esp32 by Espressif Systems 2.0.17.
Select ESP32 Dev Module, CPU 240 MHz, flash DIO/40 MHz/4 MB, default
partitions, PSRAM disabled, Upload Speed 115200, Port COM7. Verify then Upload.
Serial Monitor 115200. Source changes require a new build; the binaries in this
ZIP do not change when a header is edited after extraction.

No electrical measurements or physical motor movement were performed by Codex.
User reports completed commissioning; no measurement evidence is fabricated.
Official flashing reference:
https://docs.espressif.com/projects/esptool/en/release-v4/esp32/esptool/flashing-firmware.html
'''
    files['README_UPLOAD.txt'] = instructions.encode()
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    manifest = {'mode': 'MOTOR_OPERATION', 'arduino_core': '2.0.17', 'board': 'esp32dev',
                'bench_release': bench_release, 'commissioning_ready': ready, 'expected_boot_inhibit': 'NONE' if ready else 'COMMISSIONING_REQUIRED',
                'physical_tests_performed_by_codex': False, 'uploaded': False,
                'offsets': {'0x1000': 'firmware/bootloader.bin', '0x8000': 'firmware/partitions.bin',
                            '0xe000': 'firmware/boot_app0.bin', '0x10000': 'firmware/firmware.bin'},
                'sha256': hashes}
    files['manifest.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    files['SHA256SUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                                       for name, data in files.items()).encode()
    temporary = archive.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    temporary.replace(archive)
    return archive, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bench-release', action='store_true',
                        help='Export the motor_bench_release build (run pio run -e motor_bench_release first)')
    parser.add_argument('--build', type=Path)
    parser.add_argument('--boot-app', type=Path, default=Path.home()/'.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    env = 'motor_bench_release' if args.bench_release else 'motor_operation'
    build = args.build or ROOT/'.pio/build'/env
    output = args.output or ROOT/'build/arduino'/('motor_operation_bench_release' if args.bench_release else 'motor_operation')
    archive, manifest = export(build, args.boot_app, output, args.bench_release)
    print('ZIP:', archive)
    print('Commissioning ready:', manifest['commissioning_ready'])
