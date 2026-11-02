# Electrical reference record — checked 2 November 2026

Primary sources support chip/interface requirements. None identifies the user's exact clone module, motor, battery or DevKit assembly. Such data remains missing. Derived harness topology, resistor selections and release conditions are engineering proposals, not claims copied from a board manufacturer.

| Primary source | Application and limit |
|---|---|
| [Espressif ESP32-WROOM-32 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf) | Module pin/electrical and boot definitions; does not define unknown DevKit USB/VIN circuitry |
| [Espressif GPIO guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html) | Input-only and pull restrictions; module-specific GPIO16/17 availability must be checked for WROOM versus PSRAM variants |
| [TI SN74AHCT244](https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf) | Exact 20-pin function map, TTL-compatible input and output loading; proposed part not currently in inventory |
| [TI SN74HC244](https://www.ti.com/lit/ds/symlink/sn74hc244.pdf) | HC input thresholds differ from AHCT; reference only, not proof the actual IBT-2 uses this chip |
| [Infineon BTS7960](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf) | Silicon requirements, thresholds and protection/current limits; no board continuous-current or buffer guarantee |
| [ST L298](https://www.st.com/resource/en/datasheet/l298.pdf) | TTL inputs/enables, channel limits, losses and diode/thermal requirements; no qualification of a clone module/heatsink |
| [TI LM2596](https://www.ti.com/lit/ds/symlink/lm2596.pdf) | Regulator requirements and thermal/load context; no guarantee of assembled-board continuous output or output OVP |
| [HC-SR04 reference supplied by SparkFun](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf) | Typical 5V module and trigger/range timing; no exact manufacturer/VOH qualification for owner's modules |

No motor or LiPo manufacturer datasheet is available. Thus no numeric fuse/ampacity/overload, battery cutoff or actual component footprint is released. The design includes functional blocks where these selections are unresolved rather than assigning fictitious ratings or terminal numbers.
