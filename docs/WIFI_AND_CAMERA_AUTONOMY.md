# Wi-Fi control and camera autonomy

This adds two things to the supervised bench-release build, without changing USB control:

1. **Wi-Fi command link.** The main ESP32 creates its own Wi-Fi network, `ROVER-CTRL`. Mission Control connects to it instead of the USB cable.
2. **Camera seek.** A Python service on the laptop detects garbage in the ESP32-CAM picture. The bridge steers the rover toward it with the brushes and conveyor on. When nothing is in view, the firmware's own obstacle-avoiding AUTO mode explores.

```text
ESP32-CAM ──Wi-Fi──┐                                ┌── Main ESP32 (ROVER-CTRL access point, TCP 3333)
                   ▼                                ▼
            Laptop on ROVER-CTRL: bridge (Mission Control) ◄── vision/rover_vision.py (detections)
```

## Safety: what did not change

- All firmware safety stays in place: ARM, the 100 ms neutral gate between directions, and the 1200 ms command deadline that disarms if commands stop.
- The bridge sends heartbeats every 200 ms over Wi-Fi exactly as over USB.
- If the Wi-Fi client disconnects, the firmware **stops and disarms immediately** (`WIFI client lost; DISARMED`). A silent radio dropout disarms within 1.2 s.
- A new Wi-Fi connection always starts disarmed. Only one laptop holds control at a time.
- Camera seek never drives forward when the front ultrasonic reading is invalid, stale, or at 35 cm or closer. It stops if detections stop arriving.
- The operator always wins. Manual, Autonomous, a held key or button, Space, DISARM and the E-stop all switch camera seek off.
- Software stop is not battery isolation. Keep the physical battery switch within reach.

## 1. Flash the Wi-Fi build to the main ESP32

Build the 8-file Arduino IDE sketch. It's the bench-release sketch plus `rover_wifi.h`:

```bash
python3 scripts/package_main_arduino.py --mode MOTOR_OPERATION --bench-release --wifi
# -> build/arduino/motor_operation_bench_release_wifi/rover_main_motor_operation_bench_release_wifi.zip
```

Or with PlatformIO: `pio run -e motor_bench_release_wifi -t upload`.

The boot log adds:

```text
WIFI AP ssid=ROVER-CTRL ip=192.168.4.1 port=3333
```

The default password is `rover-collector`. To change it, add these lines to `rover_build_config.h` (at least 8 characters):

```cpp
#define ROVER_WIFI_PASSWORD "your-password"
```

Power the ESP32 from the 5 V buck to **VIN** and **GND** once the USB cable comes off.

## 2. Put the ESP32-CAM on the same network

The camera firmware doesn't change. In `camera/include/secrets.h` (or the `rover_camera` sketch settings), set:

```cpp
#define CAMERA_WIFI_SSID "ROVER-CTRL"
#define CAMERA_WIFI_PASSWORD "rover-collector"
#define CAMERA_TRUSTED_NETWORK "192.168.4.0"
#define CAMERA_TRUSTED_MASK "255.255.255.0"
```

Flash the camera, and read its address from its serial log (`Camera IP 192.168.4.x`).

## 3. Connect Mission Control over Wi-Fi

1. Join the laptop to the Wi-Fi network **ROVER-CTRL**. The laptop has no internet while it's on this network.
2. Start Mission Control: `npm run build` then `npm start`, then open `http://127.0.0.1:8787`.
3. Under **Control source**, choose **Main ESP32 · Wi-Fi**. The address is `192.168.4.1`. Click **Connect rover**.
4. Under **Camera IPv4**, enter the camera address and click **Connect camera**.

## 4. Start the vision service

Do this once, **while the laptop still has internet** (YOLO downloads its weights on the first run):

```powershell
cd C:\Users\karam\autonomous-garbage-collector-
py -m venv .vision
.vision\Scripts\pip install -r vision\requirements-yolo.txt
.vision\Scripts\python vision\rover_vision.py --source 0 --show
```

The last command tests YOLO with the laptop webcam. Close the window with `q`. If YOLO is too heavy for the laptop, install only `vision\requirements.txt`. The service then uses the colour-blob detector: colourful wrappers, cans and bottles on a plain floor.

Then, on ROVER-CTRL with the camera connected in Mission Control:

```powershell
.vision\Scripts\python vision\rover_vision.py --show
```

Mission Control's camera panel now shows `Garbage detection (yolo): bottle 82%`, with boxes drawn over the video.

Useful options:

| Option | Meaning |
|---|---|
| `--detector blob` | Force the light colour detector |
| `--classes bottle,cup` | Which YOLO classes count as garbage (`all` for everything) |
| `--model my_litter.pt` | A custom-trained YOLO model (for example one trained on the TACO litter dataset) |
| `--conf 0.5` | Minimum confidence |
| `--fps 5` | Detection rate |
| `--camera http://192.168.4.2` | Read snapshots straight from the camera instead of through the bridge |

## 5. Run camera seek (wheels off the ground first)

1. Connect the ultrasonic sensors. Camera seek and firmware AUTO both refuse to move with invalid sensors.
2. Click **ARM**, then **Camera seek**. The bridge requests **CLEAN ON**. Brushes and conveyor run only while driving forward.
3. The status under the drive buttons shows what it's doing:

| Phase | Meaning |
|---|---|
| `ALIGN LEFT` / `ALIGN RIGHT` | A short turn pulse toward the target, then a wait for a newer frame |
| `APPROACH` | Target centred: driving forward with brushes and conveyor |
| `BLOCKED` | Front obstacle at 35 cm or closer, or front sensor invalid: stopped |
| `WAITING` | Target just lost, or no detections arriving: stopped |
| `EXPLORE` | Nothing in view for 1.5 s: firmware AUTO cruise with ultrasonic obstacle avoidance |

4. To stop, press **Manual**, **Space**, **DISARM**, or the E-stop. Or pull the battery switch.

## Tuning notes

Steering constants live in `apps/rover-bridge/src/vision.ts`: centre band, turn pulse, front stop distance, and freshness limits. The front ultrasonic usually sees tall items (bottles) as obstacles, so camera seek stops 35 cm short of them. Flat litter under the sensor's beam is collected. Measure on your floor before raising speeds or lowering the stop distance.

## Verification performed (software only)

- The ESP32 compiles with Wi-Fi: `pio run -e motor_bench_release_wifi`.
- The host simulator of the real firmware, with a loopback Wi-Fi stub, was driven through the real bridge over TCP. Drive, clean, heartbeat, and link loss all checked: link loss gives an immediate stop and disarm.
- Camera seek was tested against the real bench firmware simulator for turning, approach with brushes, exploring in AUTO, and operator takeover.
- Browser tests cover the dashboard Wi-Fi source and the full camera-seek flow.
- Python tests cover payload bounds and sanitizing, and blob detection on synthetic frames.

None of this was tested on physical hardware. Test with the wheels off the ground first.
