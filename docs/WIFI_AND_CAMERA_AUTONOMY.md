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
#define CAMERA_HOSTNAME "rover-camera"
#define CAMERA_STATIC_IP "192.168.4.200"
```

`CAMERA_STATIC_IP` is optional. With it, the camera always uses `192.168.4.200`, so the address in Mission Control never changes. It must be inside the trusted network; `.200` is outside the range the rover hands out (from `.2`). Without it, the camera takes the next free address, which can change between power-ups.

Flash the camera, and check its serial log shows `Camera IP 192.168.4.200; trusted=1`. Remove the GPIO0-to-GND upload jumper and power it from 5 V and GND on a buck output.

## 3. Connect Mission Control over Wi-Fi

1. Join the laptop to the Wi-Fi network **ROVER-CTRL**. The laptop has no internet while it's on this network.
2. Start Mission Control: `npm run build` then `npm start`, then open `http://127.0.0.1:8787`.
3. Under **Control source**, choose **Main ESP32 · Wi-Fi**. The address is `192.168.4.1`. Click **Connect rover**.
4. Under **Camera IPv4**, enter the camera address (`192.168.4.200` with a fixed IP) and click **Connect camera**. Mission Control remembers it.

### Open Mission Control on phones and other laptops

Share mode lets any phone, tablet or laptop on the `ROVER-CTRL` Wi-Fi open Mission Control by scanning a QR code. The operator laptop still runs Mission Control and the vision service.

1. On the operator laptop, double-click **`Mission Control.bat`** in the project folder. It builds, starts Mission Control with sharing, and opens the browser. Or run `npm run build` then `npm run share`.
2. The command window and the **Open on another device** panel in Mission Control show a QR code and a link like `http://192.168.4.3:8787/?key=...`.
3. On the phone: join the `ROVER-CTRL` Wi-Fi, then scan the QR code with the camera. Mission Control opens. The phone remembers access, so next time open `http://192.168.4.3:8787` directly. The laptop's address can change; the QR code always shows the current one.

How access works:

- The link contains a secret key, saved in `.rover-share-key` on the laptop. Devices without it get "scan the QR code" and nothing else. To revoke access for every device, delete `.rover-share-key` and restart. A new key and QR code are created.
- Only one device controls at a time. Another device sees **Another device is controlling the rover** with a **Take control** button. Taking control **stops, disarms and disconnects** the rover first; the new operator clicks **Connect rover** and **ARM** again.
- The camera video plays on one device at a time (an ESP32-CAM limit); the newest viewer takes it over. Garbage detection keeps running regardless.
- Plain `npm start` is unchanged: only the laptop itself can open Mission Control.

On Windows, the first `npm run share` shows a **Windows Defender Firewall** prompt for Node.js. Tick **both Private and Public networks** and click **Allow**, because Windows treats `ROVER-CTRL` (no internet) as a public network. If phones can't connect, open *Windows Security → Firewall → Allow an app through firewall* and tick Public for Node.js.

On Android, if the phone says the Wi-Fi has no internet, choose **Stay connected**. Turn off mobile data if the page still doesn't load.

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

Mission Control's camera panel now shows `Garbage detection (yolo-taco): litter 82%`, with boxes drawn over the video.

### The TACO litter model

`vision/models/taco_litter.pt` is YOLOv8n fine-tuned on [TACO](http://tacodataset.org) (1500 photos of real litter, CC BY 4.0). All 60 TACO categories become one class, `litter`: wrappers, bags, cigarette butts, bottle caps, cans, cartons, paper, straws, and so on. The stock COCO model only knows bottles, cups and food. `rover_vision.py` uses the TACO model automatically when the file is present. To compare with the stock model, use `--model yolov8n.pt`.

The shipped model was trained for 60 epochs at 320 px on CPU (1269 training images, 231 held out). On the held-out images: precision 0.72, recall 0.39, mAP50 0.44, mAP50-95 0.28. It found litter in 209 of the 231 held-out photos, and nothing on synthetic plain and tiled floors. Recall is limited mainly by very small items (cigarette butts, bottle caps) at 320 px. Items close to the rover fill more of the frame and are found more reliably. The model is derived from TACO (annotations CC BY 4.0; images under their individual Flickr and OpenLitterMap licences).

To retrain, for example with more epochs or a GPU:

```bash
python scripts/train_taco.py --epochs 100        # add --device 0 for a GPU
```

It downloads TACO into `build/taco`, trains at 320 px (the size `rover_vision.py` uses), and replaces `vision/models/taco_litter.pt`. TACO photos are mostly taken from standing height. If detection is weak from the rover's low camera, add your own floor photos labelled in YOLO format to `build/taco/images/train` and `labels/train`, then retrain.

Useful options:

| Option | Meaning |
|---|---|
| `--detector blob` | Force the light colour detector |
| `--classes bottle,cup` | Which YOLO classes count as garbage (`all` for everything). Default: every class of the litter model |
| `--model yolov8n.pt` | Use the stock COCO model instead of the TACO litter model |
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
