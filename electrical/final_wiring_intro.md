# Final wiring package E1 — ESP32 waste collection rover

**DESIGN HOLD: this is a complete terminal-level proposed harness, not an electrically released assembly. No physical wire, driver rating or motor-power operation is marked approved.** All working GPIOs are preserved. Missing protection parts must be obtained and exact module/current specifications resolved before the affected connections are made or energized. The available inventory alone cannot safely complete this circuit.

Use [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md) in sequence. Every component, terminal, net and connection is defined in `electrical/design.json`, with generated `connections.csv`, `terminal_map.csv` and `bom.csv`. The generated tables below and drawings use the same source. SVGs are editable vector sources; PDFs are print exports. KiCad is not installed; no KiCad/ERC, SPICE, PCB layout or footprint validation is claimed. Module drawings are generic terminal symbols, not guessed connector orientations. Generic safety blocks define required functions; their port names are **not vendor pin numbers** and cannot be wired until mapped to selected hardware.

## Drawing set

- [Combined schematic, wiring diagrams and connection tables](diagrams/electrical_package.pdf)
- [Complete terminal-level schematic, all sheets](diagrams/complete_schematic.pdf)
- [Color-coded physical harness layout](diagrams/physical_wiring.pdf)
- [ESP32 functional pin chart](diagrams/esp32_pinout.pdf)
- [Motor-driver and seven-motor diagram](diagrams/motor_drivers.pdf)
- [Battery/power distribution](diagrams/power_distribution.pdf)
- [Sensor protection wiring](diagrams/sensor_wiring.pdf)
- [Independent E-stop and manual power-arm circuit](diagrams/emergency_stop.pdf)
- [All SVG sources and previews](diagrams/INDEX.md)

Red = positive supply; black = ground; blue = control; green = sensor/sense signals; orange = H-bridge motor outputs. Thick lines are high-current paths; thin lines are signal/logic paths. Dashed borders/lines identify planned or blocked additions, never permission to omit them. Identical net labels join across schematic sheets; crossing lines alone are not a junction. Harness bundles on the layout sheet contain separately labeled conductors, not a single shared signal. A functional ESP32 pin chart cannot establish left/right header position on an unidentified DevKit variant.

## Release/status definitions

- **Firmware mapping verified** means code, generated Wokwi sketch and host/build checks agree. It does not qualify electrical levels.
- **PROVISIONAL** means a terminal relationship is defined but exact board/physical checks remain.
- **BLOCKED_MISSING** means conditioning/protection or a selected safety assembly is unavailable. Do not fit a bypass wire.
- **BLOCKED_RATING** means current, voltage, interrupt capacity, wire sizing or manufacturer data is missing.
- **NO CONNECT / RESERVED** terminals are individually insulated and unused.

There are no physically APPROVED rows. Stock module names do not prove their terminal order, input buffer, regulator circuit, diode network or current capability. For a substitute part, revise the netlist and rerun its structural checks before construction. [ELECTRICAL_BLOCKERS.md](ELECTRICAL_BLOCKERS.md) is the open-release checklist.

## Preserved ESP32 interface and waveform behavior

GPIO16/17 = left RPWM/LPWM; GPIO18/19 = right RPWM/LPWM. GPIO14 remains the single firmware enable. GPIO21/22 = L298N channel A IN1/IN2; GPIO23/25 = channel B IN3/IN4. Front TRIG/ECHO = 32/34; left = 33/35; right = 13/36 (VP). GPIO27 = active-HIGH healthy feedback with firmware internal pull-down. GPIO26 and GPIO39/VN are unused. No camera GPIOs or power are assigned. Header position is not inferred from GPIO number.

The firmware uses four non-overlapping 1.2 kHz, 8-bit wheel PWM outputs (forward/reverse/turn commands); duty is 150/255 for drive and 140/255 for turns. Hardware polarity/rotation is unverified. A 100 ms neutral interval disables outputs before a new motion. AUTO turns target 540 ms enabled, then stopped settling and fresh sensor reassessment; repeated blocked attempts are bounded. Brushes and conveyor have independent forward-only requests, active only during actual armed forward motion. IN2/IN4 remain LOW. Shared EN means an inactive L298 channel with IN1=IN2=LOW is braked while wheels are moving; stopped EN=LOW disables both channels. This is not independent auxiliary speed control. [Turning details](TURNING_REVIEW.md).

Software boot is DISARMED; GPIO14 is driven LOW when setup starts. GPIO14's reset pull-up and high-impedance intervals mean software alone does not establish a safe power ramp. Keep K1 normally open until rails and EN are checked. Emergency input LOW or ESTOP/STOP latches a disarm; sensor invalidity/staleness disarms AUTO. The independent circuit is required if the MCU is unresponsive. [Espressif pin/electrical specification](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf).

## U1 and safe shared enable — additional hardware, not installed

The physical plan inserts a **non-inverting SN74AHCT244N** on the four wheel PWM lines, GPIO14 EN and three TRIG lines. A 5 V AHCT input accepts 3.3 V logic, while a 5 V HC input buffer must not be assumed compatible with ESP32 HIGH. This also gives full 5 V trigger levels. U1 is not an arbitrary bidirectional level-shifter module. Its physical 20-pin functions are from TI; no PCB footprint is assigned. Exact BTS board VCC=5 V and input=5 V acceptance must still be established.

| ESP32 signal | U1 input pin | U1 output pin | Destination |
|---|---|---|---|
| GPIO16 | 2 / 1A1 | 18 / 1Y1 | Left RPWM |
| GPIO17 | 4 / 1A2 | 16 / 1Y2 | Left LPWM |
| GPIO18 | 6 / 1A3 | 14 / 1Y3 | Right RPWM |
| GPIO19 | 8 / 1A4 | 12 / 1Y4 | Right LPWM |
| GPIO14 | 11 / 2A1 | 9 / 2Y1 | S2 EN NC contact, then all six EN receivers |
| GPIO32 | 13 / 2A2 | 7 / 2Y2 | Front TRIG |
| GPIO33 | 15 / 2A3 | 5 / 2Y3 | Left TRIG |
| GPIO13 | 17 / 2A4 | 3 / 2Y4 | Right TRIG |

U1 pin20 -> protected V5_LOGIC; pin10 -> logic GND; active-low OE pins1/19 -> pin10/GND; 100 nF bypass close to pins20/10. R1-4/R6-8 are 10k input pull-downs. **R5 is 2.2k from GPIO14/U1 pin11 to GND** to dominate the reset pull-up. R9-12 are 10k at L298 inputs; R13-18 are six separate 10k EN pulls at receivers; R19-22 are 10k at the four BTS PWM receivers. R29 is 10k at GPIO27. They are additional parts, not presently stocked. Module hard-HIGH links must be removed; do not short a GPIO or buffer output against a supply jumper.

At 5 V, six EN pull-downs draw 3.0 mA (about 3.182 mA at 5.25 V with 1% low resistance), **before actual module input loading/pull-ups**. TI specifies +/-8 mA output drive under its stated conditions; verify summed receiver load and worst-case VOH/VOL against the exact boards. A pull-up left on a clone can defeat disable behavior. Scope both sides of the S2 enable contact and every EN terminal through startup, reset, unplugging, rail faults and brownout. Inputs LOW and six downstream pulls provide a planned disabled default, not proof of glitch-free power-on. [AHCT pinout/limits](https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf), [HC threshold reference](https://www.ti.com/lit/ds/symlink/sn74hc244.pdf).

## Motors and driver modules

BTS7960 left: B+ from fused switched LEFT_SUPPLY, B- heavy return, VCC from qualified V5_LOGIC, GND referenced locally to B- after confirming the board bond; RPWM/LPWM from U1; both enables from EN_DRIVER_5V. R_IS/L_IS are individually insulated. M+/M- feed motors M1/M2 **in parallel**, each A lead through its own DC-rated fuse FM1/FM2. Right board is identical for M3/M4. Do not connect motor terminals to battery negative or chassis. Do not parallel the two driver outputs. If a side's motors oppose physically, reverse one motor's A/B leads during later guarded commissioning and update its wire record.

The chip's advertised current/current limiting is not a continuous module rating. Each board must sustain both motors' combined running/start/stall demand within its actual PCB, connector, device and heatsink limits. No current sensing is wired into firmware. Fuse curves must coordinate with the shortest tolerable overload, not just typical running current. [Infineon chip specification](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf).

**One L298N only:** IN1/IN2 -> GPIO21/22; IN3/IN4 -> GPIO23/25; ENA/ENB -> the same buffered, hardware-gated EN_DRIVER_5V. Remove both EN jumpers. Vs/+12V -> AUX_SUPPLY. For the common regulator-equipped board, its onboard regulator must be disabled according to its actual schematic before using its 5V terminal as an external logic input; `5V-EN` is different from ENA/ENB. If that cannot be established, do not connect external 5 V. Check correct and adequately rated recirculation diodes; missing paths require a qualified diode network. Do not put a single flyback diode across a reversible motor.

OUT1/OUT2 -> brushes M5/M6 in parallel, each A lead through FM5/FM6. OUT3/OUT4 -> conveyor M7 through FM7 in its A lead. Both brushes share speed/polarity electrically; one may need reversed motor leads for inward sweeping. Conveyor voltage is **TBD**, not assumed 12 V. Suitability is blocked until `I_A = I_brush1 + I_brush2` and conveyor demand are established simultaneously with total heat dissipation. ST's 2 A DC/channel is an absolute maximum, not a module continuous allowance. Its maximum 4.9 V bridge drop at 2 A implies about 9.8 W/channel at that point. Do not allocate the headline total current to channel A. [ST L298 specification](https://www.st.com/resource/en/datasheet/l298.pdf).

No driver is approved from motor voltage/RPM alone. At minimum complete the [current worksheet](../electrical/current_budget.csv). If startup/stall or combined heat exceeds a verified derated limit, the existing arrangement is unsuitable and must remain disconnected. Motor-lead fuses protect leads only when correctly selected; they do not automatically provide sufficiently fast semiconductor or motor-jam protection. A coordinated overload/temperature/current-protection solution is required if motor/driver tolerances cannot cover the fault. Do not assume on-chip current/thermal protection is a normal operating strategy.

## Sensor protection — blocked physical ECHO connections

US_F / US_L / US_R: VCC -> qualified protected V5_LOGIC, GND -> logic return, TRIG -> U1 output7 / 5 / 3 respectively. Exact HC-SR04 variant is unknown. For **each** ECHO fit a separate divider:

```text
sensor ECHO ---- 2.2k, 1% ----+---- GPIO34 / 35 / 36 (one sensor per GPIO)
                            |
                        3.3k, 1%
                            |
                           GND
```

R23/R24 = front, R25/R26 = left, R27/R28 = right; first resistor is series upper, second is node-to-GND lower. These six resistors are **missing**. Never fit a direct ECHO bypass. Nominal 5.0 V high gives 3.0 V; with ECHO highs assumed to follow 4.75-5.25 V and resistor tolerances, calculated node high is 2.827-3.175 V. This calculation does not establish the unknown module's real VOH/VOL. Independently measure its actual high, low, overshoot and pulse shape before connecting the ESP32; confirm HIGH exceeds 0.75*actual ESP32 VDD and maximum stays within the GPIO limit. A generic TTL-high spec alone does not guarantee a sufficiently high divided signal. If unsuitable, select a documented translator instead and revise the model.

A divider does not protect against a buck passing battery voltage: OV2 must qualify the logic/sensor supply and fault response. Buck converters regulate power, not ECHO logic levels. Three local 100 nF ceramics are proposed. Wokwi remains resistor-free with direct virtual ECHO wires and virtual LEDs; **that circuit is a simulation abstraction**, never the physical assembly reference. [HC-SR04 supply/timing reference](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf).

## Power architecture, protection and grounds

BT1 pack+ -> adjacent F0 -> S0 load isolator -> **P1 high-side protection assembly** -> TB_POS. P1 must monitor all three cells and enforce battery-specific limits; its functional CELL0..3 labels are **potentials, not balance-connector pin order**. Fuse/sense-lead protection, thresholds and connector mapping must follow the eventual protection manufacturer. Do not substitute an unidentified low-side BMS into this common-ground/USB design. P1 is a missing selection, not a fabricated board pinout. Disconnect the balance connector as well as main battery connector for unpowered work; S0 does not make cell-tap wiring safe.

From TB_POS: separately fused F1 -> BUCK1 -> OV1 -> **V5_MCU = 5.0 V target** -> approved ESP32 regulated-5V/VIN input. F2 -> BUCK2 -> OV2 -> **V5_LOGIC = 5.0 V target** -> sensors/U1/qualified driver logic. OV1/OV2 are missing independent OVP/OCP/supervision assemblies. Their required isolated fail-open power-good contacts are in the K1 coil chain; select actual devices/interfaces before wiring. Qualify their threshold accuracy, transient response, load and default state; their functional names do not imply a commercial module with those pins exists. A healthy output must stay within the design's qualified 4.75-5.25 V envelope, including tolerances. Modules/MCU may impose tighter limits. Do not assume LM2596 thermal/current limiting provides output overvoltage or cell-level protection.

From TB_POS: K1 normally-open main contact -> MOTOR_SWITCHED -> FL/FR/FA -> the two BTS B+ inputs and L298 Vs. All seven motor lead fuses and appropriately sized returns are shown. No motor passes through a buck, ESP32, Dupont lead, USB cable or solderless breadboard. High-current motor outputs are orange, not fixed positive rails. Battery 11.1 V nominal can reach 12.6 V for conventional 3S chemistry; confirm the actual label and every motor/module tolerance, including no-load voltage and regenerated transients. PWM duty is not a substitute for a motor's voltage rating.

Use TB_GND as power-return star. Driver B-/L298 GND return by dedicated branch-rated conductors. Treat BTS GND-to-B- and buck IN-/OUT- bonds as manufacturer/continuity checks, not permission for a second thin parallel motor-return wire. MCU ground returns to BUCK1 OUT-; sensors/U1 logic to BUCK2 OUT-. All share the electrical GND reference. Keep motor current out of logic ground leads and the ESP32/PC path. Separate motor leads from sensor wiring; twist motor pairs, keep switching loops short, secure insulated terminals and verify heatsink/case/chassis isolation. Do not use chassis as a motor return. No wire gauge is chosen without length/current/ambient data.

C_BL/C_BR/C_BA local reservoir capacitors and Z_L/Z_R/Z_A clamps on the load side of each branch fuse are provisional selections: capacitance, ESR, working voltage, standoff/clamp voltage and energy must be chosen together from measured ripple/regeneration and motor/module limits. A buck generally must not be assumed to absorb regenerated energy. Fuses cannot clamp transients. Verify actual board flyback and bypass components before adding/replacing anything. The ESP32-CAM is reserved, completely disconnected and excluded from today's supply budget.

### Buck adjustment and USB

Using a suitably current-limited isolated bench source later (battery and loads disconnected), check polarity, connect IN+/IN-, and measure OUT+/OUT-. Adjust each to 5.00 V before any electronics are attached. Verify separately under an appropriate dummy load, then through OV1/OV2; record ripple, peak/transient response and temperature at the measured load budget. A multimeter cannot establish fast ripple/overshoot; use suitable instruments where needed. Confirm common-negative continuity, supply margin and OVP response. Module continuous capacity is not established by the LM2596 chip's 3 A headline. [TI LM2596 specification](https://www.ti.com/lit/ds/symlink/lm2596.pdf).

Do not parallel BUCK1/2 positive outputs. Use only a board-approved ESP32 input. Do not connect regulated 5 V to 3V3 or battery to VIN. USB-only programming uses disconnected external power/signal harnesses. Later serial testing with bucks requires a verified board-supported USB isolation/data arrangement or a qualified 3.3 V UART adapter with its VCC disconnected; verify actual circuitry instead of assuming 'data-only cable' behavior. Do not drive unpowered modules through GPIOs unless documented safe; keep EN low, establish logic rails first and verify all power sequencing.

### Independent E-stop and manual power-arm circuit

The missing K1 DC contactor needs a rated main NO contact, coil compatible with the complete loaded pack range, and **two independent NO auxiliary contacts**: seal-in and isolated sense. Exact part, coil current/suppression, contact DC interrupt ratings and terminal numbers remain TBD. Generic diagram names describe roles, not vendor markings. S2 is latching with three electrically separate NC contacts: one in the coil supply, one in 3.3 V feedback, one in buffered 5 V EN. Verify low-current contact operation/wetting and isolation from the coil circuit. S3 is a deliberate momentary normally-open **hardware motor-power ARM**, not the serial ARM command.

Coil route: FK -> OV1 healthy contact -> OV2 healthy contact -> S2 coil NC -> (S3 NO in parallel with K1 seal-in NO) -> K1 A1; K1 A2 -> GND. Z_COIL is selected from K1 manufacturer guidance; a clamp can change release time. Pressing S2 opens the coil and EN regardless of MCU; K1 removes **all three drivers' motor power**. Releasing S2 alone cannot close a dropped seal-in circuit when S3 is released. Stored bus energy still needs measurement; power removal is not proof of immediate mechanical stop. A held/stuck S3, welded contact, shorted feedback or failed supervisor is not covered by this single-channel functional circuit. Select a monitored reset/safety-control solution if required by the actual risk assessment; no safety integrity/category certification is claimed.

Feedback route: ESP32 3V3 -> S2 sense NC -> **separate K1 sense NO** -> GPIO27, with R29 and internal pull-down. Thus GPIO27 is LOW while K1 is unarmed. Physical boot intentionally latches ESTOP even though Wokwi's healthy switch can start HIGH. For later commissioning, with motor loads safely disconnected and EN measured LOW: establish logic rails, deliberately power-arm K1 with S3, verify GPIO27 HIGH, then send `RESET`, `ARM`, and the desired mode. S3 does not send a motion command. After any rail/stop drop, do not power-arm until software is disarmed and EN is measured LOW. This normal-operation procedure is not a fault-tolerant guarantee that reset can never cause motion under arbitrary MCU failure.

**Serial STOP/ESTOP and DISARM disable firmware EN/PWM but do not open K1 or make the motor bus dead.** K1 is opened by the physical S2/rail-permissive circuit. Isolate power and verify discharge before wiring; never use a serial stop as an electrical isolator.

## Open selections: fuse/current/wire worksheet

Every F0/FL/FR/FA/F1/F2/FK/FM1..FM7 current, voltage and interrupt rating is **TBD**, not 30 A by default. Coordinate normal starting pulses, actual source fault current, time-current/I-squared-t curves, the smallest protected pigtail/connector, driver survival and motor overload time. Record both brush currents summed for channel A and simultaneous conveyor heating. Per-motor fuses do not increase driver capacity. Wire gauge/length, connector type and crimp ratings remain TBD from that evidence and installation conditions. If per-lead protection is redundant after a reviewed alternative, revise the design explicitly; do not silently omit a shown fuse.

Battery discharge capability needs actual continuous C rating/condition, not just 3300 mAh. Loaded current budget, pack cell limits, contactor coil range, charger chemistry and physical battery protection are unresolved. Use the manufacturer's balance-charge and storage instructions; do not charge with the rover attached. This package cannot declare the shared L298N or the rover's power system suitable before those entries are completed.

## Generated connection tables

The CSV is the same information in filterable form. `INTERNAL_VERIFY` rows describe a required existing module bond to inspect, not a new external jumper. Ground routing in these rows matters: do not create a thin parallel path around a heavy motor return. Every terminal also appears in `terminal_map.csv`, including no-connect pins. The complete schematic uses identical net names.
