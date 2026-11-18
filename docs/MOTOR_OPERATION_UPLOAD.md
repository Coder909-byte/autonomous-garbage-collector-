# Main ESP32 MOTOR_OPERATION upload preparation

Prepared 18 November 2026. This report supersedes earlier software build results
for this package, without rewriting historical electrical handover evidence.

## Current release status

The user reports completed continuity, fuse, DC disconnect, logic-level interface
and motor-current checks, and states that all commissioning checks passed.
The existing local edit sets all six flags in `include/rover_commissioning.h` to
true. Those flags and the header were preserved exactly.

The retained commissioning record identifier is still `""`. The implemented
condition is:

```cpp
driverInterface && motorPowerProtection && independentDisconnect &&
failOff && supplyAndGround && motorCurrentAndThermal && record && record[0]
```

Consequently, the actual compiled result is **commissioningReady:false** and
**COMMISSIONING_REQUIRED**. MOTOR_OPERATION is selected correctly. ARM remains
rejected, PWM is clamped to zero and driver enable stays LOW. This artifact is
compiled and uploadable for inhibited USB/sensor validation; it is **not released
for powered wheel operation**. No electrical test results were invented.

The missing release input is the existing retained record's path or identifier
covering all six conditions, including fail-off/reset/brownout and supply, common
ground and USB backfeed checks. That identifier must be supplied before changing
the final field and rebuilding the motor-enabled artifact. It is not a firmware
build error. Editing a source header after export does not update the binaries.

## Exported files

- `build/arduino/motor_operation/rover_main_motor_operation.zip`
- `~/Desktop/rover_main_motor_operation.zip` (identical copy)

Each ZIP contains seven matching Arduino source/header files; compiled main-ESP32
bootloader, partitions, boot_app0 and application images; `manifest.json`,
`SHA256SUMS.txt` and `README_UPLOAD.txt`. The manifest includes actual compile-time
readiness and payload hashes. No camera firmware, camera credentials or host-only
qualification binary is exported. ZIP CRCs, hashes and source/binary identity are
verified. `scripts/package_motor_upload.py` reproduces this export after building
the `motor_operation` PlatformIO environment.

## Flash the compiled images on the Dell G15

1. Disconnect motor power for programming. Stop Mission Control with Ctrl+C and
   close Arduino/PlatformIO Serial Monitor. Connect the **main ESP32** USB and
   confirm its port is COM7. Leave the separate ESP32-CAM alone.
2. Extract the Desktop ZIP to a new folder, then open PowerShell in that folder.
   Python 3 is required for this compiled-image procedure:

   ```powershell
   py -3 -m pip install esptool==4.9.0
   $m = Get-Content .\manifest.json -Raw | ConvertFrom-Json
   foreach ($p in $m.sha256.PSObject.Properties) { if ((Get-FileHash -Algorithm SHA256 -LiteralPath $p.Name).Hash.ToLowerInvariant() -ne $p.Value) { throw "Hash mismatch: $($p.Name)" } }
   py -3 -m esptool --chip esp32 --port COM7 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 4MB 0x1000 firmware/bootloader.bin 0x8000 firmware/partitions.bin 0xe000 firmware/boot_app0.bin 0x10000 firmware/firmware.bin
   ```

   The final command is one line. If Connecting stalls, hold BOOT until writing
   starts. Flash layout and tool syntax follow the
   [Espressif esptool v4 documentation](https://docs.espressif.com/projects/esptool/en/release-v4/esp32/esptool/flashing-firmware.html).
3. Open Serial Monitor at **115200 baud** with newline. Confirm
   `READY MOTOR_OPERATION DISARMED`, protocol-v1 TEL, `armed:false`, `en:false`
   and `applied:0`. This export still reports `commissioningReady:false` and
   `COMMISSIONING_REQUIRED`, as explained above. Close Serial Monitor afterwards.
4. With the updated Mission Control files on the Dell, run `npm run build`, then
   `npm start` at the project root. Open `http://127.0.0.1:8787`, Ctrl+F5, select
   Main ESP32 USB serial, COM7 and Connect rover. Wait for Protocol ready.
   A released build must report `commissioningReady:true`, `inhibit:NONE` and
   clear software E-stop before ARM. After explicit ARM confirmation, W/S/A/D
   are press-and-hold; release stops. No source change or reconnect restores ARM.

Arduino IDE alternative: open `rover_main/rover_main.ino`; use **esp32 by
Espressif Systems 2.0.17**, ESP32 Dev Module, CPU 240 MHz, DIO/40 MHz, 4 MB,
default partitions, PSRAM disabled, Upload Speed **115200**, Port **COM7**.
Verify then Upload, and monitor at 115200. This rebuilds the packaged sources.

## Automated verification

- PlatformIO MOTOR_OPERATION build: passed, Arduino-ESP32 2.0.17.
- Independently compiled exported Arduino sketch: passed with core 2.0.17.
- Native firmware tests: 125 passed across protected, bench, inhibited motor and
  host-only qualified motor fixtures. Coverage includes ARM/DISARM, S,
  STOP/ESTOP/reset, all four directions, neutral intervals, PWM/enable ordering,
  manual/AUTO command timeout, serial overflow and driver-disable behavior.
- Offline Simulator remains independent of commissioning. A first-keypress race
  was addressed by installing the keyboard gate in a layout effect, in the same
  UI commit that enables its direction buttons.
- Full Python suite: 61 passed, including compiled-package inventory and hash
  tests. Bridge/dashboard suite: 134 passed. Browser suite: 10 passed, including
  simulator ARM, all W/A/S/D directions, source switching and inhibited physical
  controls. Bridge/dashboard builds and production smoke check also passed.
- Full test logs, build output, ZIP verification and preservation hashes are
  under `artifacts/motor-operation-final/`.

No GPIO assignments, canonical motor firmware logic or ESP32-CAM files were
changed. PROTECTED_ROVER behavior is retained; USB_BENCH_DIAGNOSTIC remains
incapable of motor output. No physical serial port was opened, no hardware was
flashed or operated, and no GitHub push was performed during preparation.
