# Separate camera installation — S1, physical HOLD

**IMPLEMENTED, HARDWARE TEST PENDING. Actual camera variant is unidentified.** The only supported firmware configuration is `CAMERA_BOARD_AI_THINKER`, PlatformIO board `esp32cam`. Do not upload until board markings, camera sensor and PSRAM are confirmed against that configuration. Other ESP32/S2/S3 camera boards need their own reviewed map. The main ESP32 GPIO header is unchanged; there is no camera signal wire to the main controller.

AI-Thinker supported internal mapping is in `camera/include/board_ai_thinker.h`: PWDN32, reset absent, XCLK0, SCCB26/27, D0..7=5/18/19/21/36/39/34/35, VSYNC25, HREF23, PCLK22. This comes from [Espressif Arduino 2.0.17 camera pin definitions](https://raw.githubusercontent.com/espressif/arduino-esp32/2.0.17/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h). These are camera-board GPIOs, a separate address space from the motor controller.

## Power branch and canonical records

Use [camera power sheet](diagrams/camera_power.pdf), [SVG](diagrams/camera_power.svg), `electrical/system_design.json` and generated `system_connections.csv` / `system_netlist.json`. E2 `design.json` / `connections.csv` remain frozen for W001-W201. The system overlay explicitly activates the formerly reserved CAM1 supply/GND ports. All added ports are functional labels awaiting actual hardware terminal mapping, not invented connector positions.

| ID | Source | Destination | Requirement |
|---|---|---|---|
| W202 | TB_POS.BUS | F3.IN | Separate fused protected-battery branch before K1 |
| W203 | F3.OUT | BUCK3.IN+ | Qualified third regulator input |
| W204 | TB_GND.BUS | BUCK3.IN- | Dedicated branch return |
| W205 | BUCK3.IN- | BUCK3.OUT- | Inspect internal common-negative bond; do not add wire |
| W206 | BUCK3.OUT+ | OV3.IN+ | Raw regulated camera 5V |
| W207 | BUCK3.OUT- | OV3.GND | Protector reference |
| W208 | OV3.OUT+ | CAM1.5V | Protected supply to verified board 5V input |
| W209 | BUCK3.OUT- | CAM1.GND | Dedicated camera return |
| W210 | OV3.OUT+ | C_CAM.1 | Local supply bypass |
| W211 | CAM1.GND | C_CAM.2 | Local bypass return |

No camera supply comes from main ESP32 3V3, existing BUCK1/2 outputs, raw LiPo, motor outputs or laptop USB. Do not parallel positive rails. BUCK3/OV3 remain unselected; a third LM2596 module is only a candidate if its actual thermal/peak/fault performance is qualified. OV3 must prevent battery fail-through and coordinate current limiting with F3 and the weakest conductor. Camera power is not switched by K1; losing video cannot energize motor outputs, and the camera does not provide a safety permissive.

Provisional sizing allocation is **5V at 1A continuous, 2A transient capacity**, not measured camera consumption. Pout=5W continuous/10W transient. At an illustrative, unverified 80% efficiency, input is 6.25W/12.5W and regulator loss is 1.25W/2.5W. Ipack=Pinput/Vpack: at illustrative 9V, 0.694A/1.389A; at 12.6V, 0.496A/0.992A. These examples neither set battery cutoff nor qualify thermal behavior. Actual camera peak duration, onboard regulator dissipation, dropout, ripple, start-up and ambient must be measured. Espressif's [chip-level supply guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html) is not a complete 5V camera-board current specification. Existing MCU/logic/motor budgets remain unknown; no shared-rail headroom is presumed.

Select C_CAM capacitance/ESR and voltage rating from regulator stability guidance, board bypassing and measured transients. Do not guess a fuse amperage. Qualify voltage at the actual camera input under Wi-Fi/capture load, wiring drop, OVP/OCP, worst input voltage and enclosed ambient. Verify that camera faults cannot raise other rails, feed USB or route motor current through laptop ground. F0/P1/master switch/distribution/battery must include the additional input allocation in their final budgets.

## Separate programming

A confirmed AI-Thinker board generally needs an external 3.3V-logic USB UART programmer or its matching dock; identify the actual board first. In a detached, approved isolated setup, programmer TX -> camera U0R, RX -> U0T, ground -> camera GND. Never apply 5V UART logic. Use a qualified 5V camera supply and a documented single power-source arrangement; leave programmer VCC disconnected when independently powered unless its maker explicitly supports the arrangement. Verify ground and supply isolation before attachment. Camera GPIO0 is a boot strap: use the actual board's programming procedure, remove the boot strap for run mode, and reset. Do not connect this programmer to main-controller motor wiring. U0R/U0T remain NC in the permanent system model.

## Physical acceptance still required

Identify board/sensor/PSRAM and programmer, qualify detached supply, test boot/init failure diagnostics, join the explicitly configured isolated WLAN, verify IP discovery and /status, capture a real JPEG, stream to laptop, measure actual frame rate/resolution/latency/heap/thermal behavior, interrupt Wi-Fi and observe bounded reconnect, unplug camera and verify UI failure, test multiple clients/busy handling, and verify motor-control operation remains independent. No test in this repository claims real video, regulator suitability or motor-power isolation.
