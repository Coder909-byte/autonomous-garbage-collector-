# Hardware requirements update — S1, 10 November 2026

**Physical assembly/power-up HOLD.** Read the unchanged [E2 purchase specification](FINAL_PURCHASE_LIST.md) first. Software completion does not qualify unknown motors, LiPo discharge capability, L298N suitability, safety hardware or USB backfeed. The older main ESP32 program is still installed.

| Addition / check | Quantity | Selection evidence needed | Result |
|---|---:|---|---|
| CAM1 identification | Existing one | Manufacturer, exact board revision, sensor, supply input, pin map, PSRAM, onboard regulator and programmer | BLOCKED BY SPECIFIC MISSING HARDWARE information |
| BUCK3 separate camera regulator | 1 additional | Actual pack min/max/fault envelope; qualified 5V, 1A continuous / 2A transient provisional capacity; stability, start-up and thermal evidence | Unselected, HOLD |
| F3 DC fuse and holder | 1 each | DC interrupt rating, inrush/peak duration and smallest branch conductor; actual fuse current TBD | Unselected, HOLD |
| OV3 independent camera protection | 1 assembly | Output OVP/OCP, fail-through withstand, qualified board supply limits, safe startup/short behavior | Unselected, HOLD |
| C_CAM supply bypass | 1 position / network | Required capacitance/ESR/voltage, actual onboard capacitors and regulator requirements | Unselected, HOLD |
| Camera supply/return harness | W202-W211 | Actual terminal mapping, conductor lengths/drop/current/temperature, insulated connectors and strain relief | No vendor pin numbers invented |
| Camera programmer/dock | 1 if absent | Confirmed board support, UART 3.3V logic, qualified power source, isolation/backfeed arrangement | Physical programmer not verified |
| Trusted local WLAN | 1 isolated network | Explicit SSID/private /24, WPA2 credentials, authorized clients; no internet forwarding | User configuration pending |
| Laptop USB supply isolation | As qualified | Existing DevKit USB + external 5V topology and ground path; USB UART or approved isolation arrangement if needed | Original HOLD retained |

[Camera wiring](CAMERA_WIRING.md) gives the provisional budget equations. The new 5W continuous / 10W transient capacity envelope is an engineering allocation, not a measured load. Do not use it to select F0/F3 or approve battery, wiring, regulator cooling or camera-board LDO without current/voltage/temperature evidence. `electrical/system_power_budget.csv` keeps these assumptions separate from unknown measured values. Existing `electrical/current_budget.csv` remains the untouched E2 worksheet.

Driver suitability remains conditional: sum both wheel motors per BTS module and both brushes on L298 channel A, including start/stall/braking current; assess simultaneous conveyor heat and bipolar drop. RPM and nominal voltage do not establish current suitability. If replacing L298N, follow its documented conditional revision and update the netlist/adapter/tests before installation. No substitute is installed or declared approved here.

Commissioning needs actual module photos/datasheets, resolved protection terminals/ratings, unpowered continuity/polarity/isolation records, qualified current-limited rail tests, motor-free physical cutoff tests, detached firmware installation, guarded individual motor direction/current tests and loaded thermal/stopping tests. Follow the existing staged E2 handover, adding the detached camera branch qualification. No LiPo power-up, firmware upload or motor energization was performed automatically.
