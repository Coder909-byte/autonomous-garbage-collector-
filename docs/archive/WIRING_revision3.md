> **SUPERSEDED HISTORICAL DOCUMENT. Do not assemble from this revision. Use [FINAL_WIRING.md](../FINAL_WIRING.md) and the E1 release blockers.**

# Physical wiring — one L298N, proposed revision 3

**Physical hardware is electrically unverified. Do not upload firmware, connect battery power or energize any motor during this software task. All three real ECHO wires remain disconnected.** The Wokwi diagram is a digital signal model and must not be copied as a physical circuit.

## Confirmed inventory and connection limits

Use the existing ESP32-WROOM-32, four wheel motors, two BTS7960 modules, three HC-SR04 modules, two brush motors, **one L298N**, conveyor motor, two LM2596 modules and 3S 3300 mAh LiPo. No second L298N or mandatory buffer IC is assumed. Resistors and level shifters are **not currently available**. No resistor components are present in Wokwi.

| Interface | Physical status with current information/parts |
|---|---|
| All three ultrasonic ECHO outputs | **DO NOT CONNECT** to ESP32. Exact manufacturer, variant and datasheet are unknown, as confirmed by the owner. There is no evidence of a 3.3 V-compatible output on these exact modules. |
| BTS7960 RPWM/LPWM and enable interface | Proposed GPIO allocation only. Confirm exact board supply, input buffer and 3.3 V VIH/VIL requirements before connection. Do not assume the BTS7960 IC's thresholds describe an IBT-2 board's input buffer. |
| Reset-safe driver enables | Not approved. No external pull-downs are available and module defaults are unknown. Firmware drives EN low once setup starts; this does not establish safe behavior before setup or during a power ramp/reset. |
| L298N channel A / both brushes | **Unverified: leave motors disconnected** until combined current and module thermal capability are established. |
| L298N channel B / conveyor | **Unverified: leave motor disconnected** until voltage, current and module thermal capability are established. |
| Independent emergency power cutoff, fusing and LiPo protection | Not confirmed in inventory. A software ESTOP cannot replace an independent motor-power disconnect; battery operation is not approved. |
| Wokwi LEDs / analyzer | Virtual diagnostic instruments only. No real LED or analyzer wiring is required. Never copy the resistor-free LED connections into hardware. |

## Final proposed GPIO map

Numbers are GPIO numbers, not physical header positions. Verify your actual DevKit header labels. This map is for WROOM-32, not WROVER/PSRAM boards reserving GPIO16/17.

| ESP32 GPIO | Signal | Proposed physical destination | Wokwi pin |
|---|---|---|---|
| 16 | Left forward PWM | Left BTS7960 RPWM, pending logic confirmation | RX2 |
| 17 | Left reverse PWM | Left BTS7960 LPWM, pending logic confirmation | TX2 |
| 18 | Right forward PWM | Right BTS7960 RPWM, pending logic confirmation | D18 |
| 19 | Right reverse PWM | Right BTS7960 LPWM, pending logic confirmation | D19 |
| 14 | Shared driver enable | Both BTS R_EN/L_EN and L298N ENA/ENB, subject to enable-interface checks below | D14 |
| 21 | Both brushes forward | L298N IN1, channel A | D21 |
| 22 | Both brushes reverse input, held LOW | L298N IN2, channel A | D22 |
| 23 | Conveyor forward | L298N IN3, channel B | D23 |
| 25 | Conveyor reverse input, held LOW | L298N IN4, channel B | D25 |
| 32 | Front trigger | Front HC-SR04 TRIG, verify actual 3.3 V trigger acceptance | D32 |
| 34 | Front ECHO input reservation | **DISCONNECTED pending exact module voltage confirmation** | D34, simulation only |
| 33 | Left trigger | Left HC-SR04 TRIG, same qualification | D33 |
| 35 | Left ECHO input reservation | **DISCONNECTED pending exact module voltage confirmation** | D35, simulation only |
| 13 | Right trigger | Right HC-SR04 TRIG, same qualification | D13 |
| 36 | Right ECHO input reservation | **DISCONNECTED pending exact module voltage confirmation** | VP, simulation only |
| 27 | E-stop healthy input | Separate NC dry contact from 3V3; internal pull-down enabled | D27 |

There are 16 unique assignments. GPIO26 and GPIO39/VN are now unused: **remove the old conveyor GPIO26/27 and E-stop GPIO39 wiring**. GPIO23/25 now control the conveyor, not a separately driven second brush. GPIO34/35/36 are input-only; GPIO27 supports the internal pull-down used here. Flash GPIO6–11, serial GPIO1/3 and boot straps GPIO0/2/5/12/15 are unused. GPIO13/14 are application I/O; do not enable JTAG. GPIO14 has a reset pull-up, so the missing hardware disable/default-low provisions are particularly important. [Espressif datasheet](https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html).

## One L298N: exact terminal assignments

Remove **ENA and ENB enable jumpers** before attaching any ESP32 enable signal. If the board has a `5V-EN` regulator jumper, identify it separately: it is not ENA/ENB. Never connect an external buck output to an active onboard regulator output.

| L298N terminal | Proposed connection |
|---|---|
| IN1 | ESP32 GPIO21 |
| IN2 | ESP32 GPIO22, firmware LOW |
| IN3 | ESP32 GPIO23 |
| IN4 | ESP32 GPIO25, firmware LOW |
| ENA | Qualified GPIO14 enable net; jumper removed |
| ENB | Same enable net; jumper removed |
| OUT1 | One terminal of brush 1 AND the corresponding terminal of brush 2 |
| OUT2 | The other terminal of brush 1 AND the other terminal of brush 2 |
| OUT3 | Conveyor terminal 1 |
| OUT4 | Conveyor terminal 2 |
| Vs / +12V | Proposed separately fused auxiliary motor branch after independent motor-power disconnect; currently disconnected |
| GND | Common ground with separate appropriately sized motor-current return |
| 5V logic terminal | Verified regulated 5 V input only if your exact board supports external logic power with its regulator disabled |

Both brushes are **in parallel across OUT1/OUT2**. They share speed and electrical polarity and cannot be controlled separately. For inward sweeping, one physically opposed brush may need its leads reversed; establish this only in a later guarded commissioning test. Do not wire a brush or conveyor terminal directly to battery negative, and do not parallel OUT1/OUT2 with OUT3/OUT4.

`BRUSH ON/OFF` controls channel A independently of `CONVEYOR ON/OFF` controlling B. `CLEAN ON/OFF` is a convenience command for both. Commands set independent requests; actual auxiliary outputs are allowed **only while armed and actually moving forward**. Both turn off during the 100 ms neutral interval, reverse, turning, stopping, disarm or emergency stop. They do not run while stationary. Shared EN does not mean the motor requests are coupled: IN1 and IN3 determine each channel independently. With EN high and both channel inputs LOW, that channel brakes instead of freewheeling. A shared EN provides no separate speed control.

### Can the L298N safely handle both brushes?

**Not established.** Channel A carries the sum of the two brush currents; channel B and the shared package must support the conveyor simultaneously. Motor voltage and RPM do not determine current.

- Record `I_A_run = I_brush1_run + I_brush2_run` and the worst simultaneous starting/jam demand, approximately `I_A_stall = I_brush1_stall + I_brush2_stall`, at the maximum allowed supply voltage.
- Obtain conveyor running/start/stall requirements and the exact module's continuous rating, heatsink/airflow, terminals, flyback diodes and overload protection. Estimate total package dissipation with **both channels loaded**.
- ST specifies 2 A DC per channel as an **absolute maximum**, with separate short-pulse limits. It is not a guaranteed safe module operating point. The datasheet gives substantial bridge voltage loss, up to 4.9 V total at 2 A; at that point one bridge can dissipate about 9.8 W. Do not use the advertised 4 A total as the allowance for the brush channel.
- If summed brush demand or shared heating exceeds a suitably derated verified capability, this arrangement is unsuitable with the existing L298N. Leave it disconnected; a driver change would then be necessary, not an assumed addition today.

No current measurement or motor-power trial was performed. A later controlled current characterization is separate work; do not stall a motor directly from the LiPo. [ST L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf).

## Ultrasonic compatibility hold

The confirmed description is only **HC-SR04**, with no manufacturer, exact variant or datasheet. A generic HC-SR04 reference specifies a 5 V module; it does not prove a special 3.3 V ECHO output on your three units. The common standard module's ECHO is a 5 V signal and must not be connected directly to an ESP32 input. [HC-SR04 reference](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf), [Adafruit's interface guidance](https://learn.adafruit.com/distance-measurement-ultrasound-hcsr04?view=all).

For **each** sensor: VCC is reserved for a verified sensor supply per the actual module specification, GND for common ground, TRIG for the proposed GPIO above, and **ECHO remains insulated/disconnected** from GPIO34/35/36. Never change the ESP32 3V3 rail or assume powering a standard module at 3.3 V fixes its interface.

Release this hold only after identifying manufacturer documentation guaranteeing ECHO VOH/VOL and maximum voltage at the intended supply, and verifying actual levels/overshoot independently of the ESP32 during a later electrical test. If it is a standard 5 V-output module, voltage reduction/translation is necessary; those parts are currently unavailable. Do not bypass this requirement. The firmware and Wokwi model can be developed without connecting any real sensor.

Wokwi connects virtual ECHO pins directly because it models digital pulses. That is **simulation-only**. The three sensors are pinged sequentially with at least 65 ms between starts, 25 ms echo timeouts, and 500 ms per-sensor freshness protection. AUTO requires three valid fresh readings and disarms on a subsequent invalid/stale sample. Real acoustic crosstalk, mounting and detection are untested.

## Wheel BTS7960 modules and shared enable

| Terminal | Left module | Right module |
|---|---|---|
| RPWM / LPWM | Proposed GPIO16 / GPIO17 | Proposed GPIO18 / GPIO19 |
| R_EN and L_EN | Proposed qualified GPIO14 enable net | Same |
| VCC | Supply required by exact board; not inferred from chip name | Same |
| GND | Common logic ground | Common logic ground |
| R_IS / L_IS | Individually insulated, unused | Individually insulated, unused |
| B+ | Fused left motor branch after independent disconnect, currently disconnected | Fused right motor branch, currently disconnected |
| B− | High-current negative return | High-current negative return |
| M+ / M− | Two left wheel motors in parallel across outputs | Two right wheel motors in parallel across outputs |

Confirm exact IBT-2/BTS7960 module input buffering. Some 5 V input-buffer arrangements do not guarantee a 3.3 V HIGH. Do not wire 5 V into an ESP32 GPIO or arbitrarily change a board's logic supply to 3.3 V. If the module cannot accept the ESP32 signals, the necessary translator is unavailable and the interface stays disconnected. The chip datasheet alone cannot qualify unknown module components.

The shared EN proposal has six loads: four BTS enables plus L298N ENA/ENB. Check fanout, any board pull-ups, reset behavior and logic thresholds before joining them. Remove any hard-HIGH enable links and establish a hardware default-disabled state independent of firmware. No external resistors are presently available to fix unsafe defaults. Do not energize motor power on the strength of a software DISARMED message.

Size each side for two summed wheel-motor currents, including simultaneous start/stall. An advertised '43 A' BTS7960 figure is not a verified continuous PCB/connector/heatsink rating. [Infineon chip datasheet](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf).

## E-stop feedback and independent power cutoff

Proposed logic feedback: **ESP32 3V3 → separate normally closed dry contact → GPIO27**. Firmware enables GPIO27's internal pull-down, so opening/breaking this circuit while firmware is running reads LOW and latches a trip. Never feed 5 V/12 V or a contactor-coil circuit into it. No external resistor is needed for this logic function, but switch availability, noise immunity and electrical behavior remain unverified. A short to 3V3 is not detected.

Wokwi uses an SPDT switch: terminal 1 → 3V3, terminal 2 → GPIO27, terminal 3 → GND. LEFT is healthy, RIGHT is E-stop. It supplies explicit digital states without resistors; it does not model contactor current, wire faults or hardware safety certification.

GPIO27's falling-edge ISR clears GPIO14 immediately in software, and the main loop subsequently clears PWM and all auxiliary outputs. The independent motor-power cutoff is still required for MCU failure: it must remove supply to **both wheel drivers and the one L298N**, using correctly rated DC switching/contactors and reviewed manual reset behavior. It must not merely turn off ESP32 power or ground. It is not confirmed in inventory, so this is a design requirement, not a claim it exists.

`STOP` and `ESTOP` both latch the software emergency stop. Releasing a switch never automatically restarts. With healthy feedback send `RESET`, then `ARM`, then `AUTO` or a manual motion command. `RESET` never arms. `S` is the separate non-latching stop/exits-AUTO command. Serial commands can wait for one 25 ms echo timeout plus processing; no physical response time or stopping distance is verified.

## Proposed power routing — no battery connection authorized

```text
3S LiPo + → correctly selected main fuse → master isolation → protected distribution
  ├─ fused logic branch → LM2596 #1 → verified 5 V → approved ESP32 5V/VIN input
  ├─ fused logic branch → LM2596 #2 → verified 5 V → qualified sensor/driver logic loads
  └─ independent E-stop motor disconnect → individually fused branches
       ├─ left BTS7960 B+
       ├─ right BTS7960 B+
       └─ the ONE L298N Vs (both auxiliary channels)
LiPo − → high-current return distribution → driver power negatives and buck IN−
Buck OUT− / ESP32 GND / sensor GND / driver logic GND → common ground
```

The two buck positive outputs must not be paralleled. Neither buck powers a wheel, brush or conveyor motor. Confirm actual module non-isolated grounding and exact board logic supply requirements. Prevent ESP32 USB/buck backfeed per the DevKit schematic; do not connect battery voltage to 5V/VIN or 5 V to 3V3. No motor power through breadboards or Dupont leads. Adjust/load-test bucks later using appropriate current-limited equipment with electronics initially disconnected; the LM2596 chip rating is not a verified assembled-module continuous capability. [TI documentation](https://www.ti.com/product/LM2596).

Conventional 3S LiPo is 11.1 V nominal and 12.6 V at full charge. Confirm chemistry/label and every motor's allowed voltage. Pack capacity alone does not establish discharge capability: current depends on its actual C rating, condition and connectors. Fuse/wire/contactor selections remain pending load currents and ratings. Check regenerative transients and suppression, not just steady voltage. Independent 3S cell-level undervoltage protection and proper balance charging are not supplied by this firmware. Obtain battery-specific limits; no battery-specific suitability approval is possible from the provided label values alone.

Physical current, power-ramp, voltage-level, protection, continuity and mechanical tests remain future work. See [TEST_MATRIX.md](../TEST_MATRIX.md) for the evidence boundary and unexecuted commissioning requirements.

The turning-state software update does not change this pin map or release any physical hold. It now targets 540 ms of enabled turn output after 100 ms neutral, followed by a stopped reassessment and bounded retries. These are software timings, not measured mechanical stopping/turning performance; see [TURNING_REVIEW.md](TURNING_REVIEW.md).
