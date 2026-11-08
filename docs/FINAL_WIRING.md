# Final wiring package E2 — ESP32 waste collection rover

**DESIGN HOLD: this is a complete terminal-level proposed harness, not an electrically released assembly. No physical wire, driver rating or motor-power operation is marked approved.** All working GPIOs are preserved. Missing protection parts must be obtained and exact module/current specifications resolved before the affected connections are made or energized. The available inventory alone cannot safely complete this circuit.

Current sectional instructions: [READY_TO_WIRE.md](READY_TO_WIRE.md); design decisions: [FINAL_GO_NO_GO.md](FINAL_GO_NO_GO.md); staged later commissioning: [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md). Every component, terminal, net and connection is defined in `electrical/design.json`, with generated `connections.csv`, `terminal_map.csv` and `bom.csv`. The generated tables below and drawings use the same source. SVGs are editable vector sources; PDFs are print exports. KiCad is not installed; no KiCad/ERC, SPICE, PCB layout or footprint validation is claimed. Module drawings are generic terminal symbols, not guessed connector orientations. Generic safety blocks define required functions; their port names are **not vendor pin numbers** and cannot be wired until mapped to selected hardware.

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

R23/R24 = front, R25/R26 = left, R27/R28 = right; first resistor is series upper, second is node-to-GND lower. E2 inserts U2 SN74LVC3G34DCU between every divider and its GPIO: front U2.1->7, left U2.3->5, right U2.6->2. U2.8 uses ESP1.3V3, U2.4 uses ESP1.GND, C_U2=100nF across 8/4, R30/R31/R32=100k from outputs to GND. The divided nodes are EF_DIV/EL_DIV/ER_DIV, not GPIO nets. Measure U2 input HIGH >=2.0V, LOW <=0.8V and input transitions <=10ns/V. U2 Ioff addresses a sensor rail live while MCU power is off; actual ramp behavior remains untested. These six resistors are **missing**. Never fit a direct ECHO bypass. Nominal 5.0 V high gives 3.0 V; with ECHO highs assumed to follow 4.75-5.25 V and resistor tolerances, calculated node high is 2.827-3.175 V. This calculation does not establish the unknown module's real VOH/VOL. Independently measure its actual high, low, overshoot and pulse shape before connecting the ESP32; confirm HIGH exceeds 0.75*actual ESP32 VDD and maximum stays within the GPIO limit. A generic TTL-high spec alone does not guarantee a sufficiently high divided signal. If unsuitable, select a documented translator instead and revise the model.

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

| ID | Component | Source terminal | Destination terminal | Signal / expected voltage | Status / route | Required protection | Verification |
|---|---|---|---|---|---|---|---|
| W001 | main pack fuse / holder | BT1.PACK+ | F0.IN | power_hc; Pack: up to 12.6 V | BLOCKED_RATING; WIRE | Main fuse adjacent to pack; insulated connector | Verify chemistry, polarity, pack C rating and connector interrupt/short-circuit capability |
| W002 | Master load isolator | F0.OUT | S0.COM | power_hc; Pack voltage | BLOCKED_RATING; WIRE | F0 protects feed | Select F0 from measured/spec start/stall currents and conductor ampacity |
| W003 | 3S high-side protection assembly | S0.OUT | P1.IN+ | power_hc; Pack voltage | BLOCKED_MISSING; WIRE | Master isolation plus P1 | Verify selected protection assembly input/output polarity and high-side topology |
| W004 | Protected positive distribution | P1.OUT+ | TB_POS.BUS | power_hc; Loaded pack voltage; up to 12.6 V | BLOCKED_MISSING; WIRE | Cell-level protection + F0 + downstream fuses | Select P1 and current ratings; do not use undefined raw BMS terminals |
| W005 | DC motor contactor | TB_POS.BUS | K1.MAIN_COM | power_hc; Loaded pack voltage; up to 12.6 V | BLOCKED_MISSING; WIRE | Cell-level protection + F0 + downstream fuses | Select P1 and current ratings; do not use undefined raw BMS terminals |
| W006 | MCU buck input fuse / holder | TB_POS.BUS | F1.IN | power_hc; Loaded pack voltage; up to 12.6 V | BLOCKED_MISSING; WIRE | Cell-level protection + F0 + downstream fuses | Select P1 and current ratings; do not use undefined raw BMS terminals |
| W007 | logic buck input fuse / holder | TB_POS.BUS | F2.IN | power_hc; Loaded pack voltage; up to 12.6 V | BLOCKED_MISSING; WIRE | Cell-level protection + F0 + downstream fuses | Select P1 and current ratings; do not use undefined raw BMS terminals |
| W008 | contactor coil fuse / holder | TB_POS.BUS | FK.IN | power_hc; Loaded pack voltage; up to 12.6 V | BLOCKED_MISSING; WIRE | Cell-level protection + F0 + downstream fuses | Select P1 and current ratings; do not use undefined raw BMS terminals |
| W009 | left driver fuse / holder | K1.MAIN_NO | FL.IN | power_hc; Pack voltage when K1 closed | BLOCKED_RATING; WIRE | Independent motor power removal | Prove E-stop drops K1, release alone does not re-latch, and stored bus energy decays |
| W010 | right driver fuse / holder | K1.MAIN_NO | FR.IN | power_hc; Pack voltage when K1 closed | BLOCKED_RATING; WIRE | Independent motor power removal | Prove E-stop drops K1, release alone does not re-latch, and stored bus energy decays |
| W011 | auxiliary driver fuse / holder | K1.MAIN_NO | FA.IN | power_hc; Pack voltage when K1 closed | BLOCKED_RATING; WIRE | Independent motor power removal | Prove E-stop drops K1, release alone does not re-latch, and stored bus energy decays |
| W012 | BTS7960 / IBT-2 left | FL.OUT | DRV_L.B+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FL; motor branch overload coordination | Verify sum of two left start/stall currents and actual IBT-2 thermal/connector capacity |
| W013 | local motor-bus reservoir | FL.OUT | C_BL.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FL; motor branch overload coordination | Verify sum of two left start/stall currents and actual IBT-2 thermal/connector capacity |
| W014 | Local driver-bus transient clamp | FL.OUT | Z_L.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FL; motor branch overload coordination | Verify sum of two left start/stall currents and actual IBT-2 thermal/connector capacity |
| W015 | BTS7960 / IBT-2 right | FR.OUT | DRV_R.B+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FR; motor branch overload coordination | Verify sum of two right start/stall currents and actual IBT-2 thermal/connector capacity |
| W016 | local motor-bus reservoir | FR.OUT | C_BR.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FR; motor branch overload coordination | Verify sum of two right start/stall currents and actual IBT-2 thermal/connector capacity |
| W017 | Local driver-bus transient clamp | FR.OUT | Z_R.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FR; motor branch overload coordination | Verify sum of two right start/stall currents and actual IBT-2 thermal/connector capacity |
| W018 | ONE L298N: A brushes / B conveyor | FA.OUT | DRV_A.Vs_12V | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FA + FM5/FM6/FM7; package thermal review | Verify combined brush current, conveyor current, per-channel and shared thermal constraints |
| W019 | local motor-bus reservoir | FA.OUT | C_BA.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FA + FM5/FM6/FM7; package thermal review | Verify combined brush current, conveyor current, per-channel and shared thermal constraints |
| W020 | Local driver-bus transient clamp | FA.OUT | Z_A.+ | power_hc; Pack voltage | BLOCKED_RATING; WIRE | FA + FM5/FM6/FM7; package thermal review | Verify combined brush current, conveyor current, per-channel and shared thermal constraints |
| W021 | LM2596 #1 | F1.OUT | BUCK1.IN+ | power_lc; Pack voltage | BLOCKED_RATING; WIRE | F1 for buck input and lead | Verify module input range and fault-current/wire coordination |
| W022 | LM2596 #2 | F2.OUT | BUCK2.IN+ | power_lc; Pack voltage | BLOCKED_RATING; WIRE | F2 for buck input and lead | Verify buck input range and module load budget |
| W023 | ESP32-WROOM-32 DevKit | OV1.OUT+ | ESP1.5V_VIN | power_lc; Regulated 5.0 V target | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | Measure output unloaded/loaded and verify actual DevKit regulated-5V input and USB backfeed path |
| W024 | SN74AHCT244N 3.3-to-5 V buffer | OV2.OUT+ | U1.20 (VCC) | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W025 | BTS7960 / IBT-2 left | OV2.OUT+ | DRV_L.VCC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W026 | BTS7960 / IBT-2 right | OV2.OUT+ | DRV_R.VCC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W027 | ONE L298N: A brushes / B conveyor | OV2.OUT+ | DRV_A.5V_LOGIC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W028 | HC-SR04 front | OV2.OUT+ | US_F.VCC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W029 | HC-SR04 left | OV2.OUT+ | US_L.VCC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W030 | HC-SR04 right | OV2.OUT+ | US_R.VCC | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W031 | local ceramic bypass | OV2.OUT+ | C_U1.1 | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W032 | local ceramic bypass | OV2.OUT+ | C_F.1 | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W033 | local ceramic bypass | OV2.OUT+ | C_L.1 | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W034 | local ceramic bypass | OV2.OUT+ | C_R.1 | power_lc; Regulated 5.0 V target; qualify 4.75-5.25 V | BLOCKED_MISSING; WIRE | Independent OVP/OCP/supervision; qualify voltage envelope and fault response | No MCU-connected 5V signal; verify ripple/load response and all actual board logic supply requirements |
| W035 | Latching E-stop / 3 isolated NC contacts | ESP1.3V3 | S2.SENSE_COM | power_lc; ESP32 3.3 V | PROVISIONAL; WIRE | MCU-derived 3V3; dry feedback and U2 only; never V5_LOGIC | Verify no connection to 5V/coil circuit and actual feedback-contact minimum current |
| W036 | SN74LVC3G34DCU ECHO isolation | ESP1.3V3 | U2.8 (VCC) | power_lc; ESP32 3.3 V | PROVISIONAL; WIRE | MCU-derived 3V3; dry feedback and U2 only; never V5_LOGIC | Verify no connection to 5V/coil circuit and actual feedback-contact minimum current |
| W037 | local ceramic bypass | ESP1.3V3 | C_U2.1 | power_lc; ESP32 3.3 V | PROVISIONAL; WIRE | MCU-derived 3V3; dry feedback and U2 only; never V5_LOGIC | Verify no connection to 5V/coil circuit and actual feedback-contact minimum current |
| W038 | 3S LiPo / connector | TB_GND.BUS | BT1.PACK- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W039 | 3S high-side protection assembly | TB_GND.BUS | P1.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W040 | ESP32-WROOM-32 DevKit | BUCK1.OUT- | ESP1.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W041 | LM2596 #1 | TB_GND.BUS | BUCK1.IN- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W042 | LM2596 #1 | BUCK1.IN- | BUCK1.OUT- | ground; 0 V reference; returns sized by branch | PROVISIONAL; INTERNAL_VERIFY | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W043 | LM2596 #2 | TB_GND.BUS | BUCK2.IN- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W044 | LM2596 #2 | BUCK2.IN- | BUCK2.OUT- | ground; 0 V reference; returns sized by branch | PROVISIONAL; INTERNAL_VERIFY | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W045 | BTS7960 / IBT-2 left | TB_GND.BUS | DRV_L.B- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W046 | BTS7960 / IBT-2 left | DRV_L.B- | DRV_L.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; INTERNAL_VERIFY | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W047 | BTS7960 / IBT-2 right | TB_GND.BUS | DRV_R.B- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W048 | BTS7960 / IBT-2 right | DRV_R.B- | DRV_R.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; INTERNAL_VERIFY | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W049 | ONE L298N: A brushes / B conveyor | TB_GND.BUS | DRV_A.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W050 | HC-SR04 front | BUCK2.OUT- | US_F.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W051 | HC-SR04 left | BUCK2.OUT- | US_L.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W052 | HC-SR04 right | BUCK2.OUT- | US_R.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W053 | SN74AHCT244N 3.3-to-5 V buffer | BUCK2.OUT- | U1.10 (GND) | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W054 | SN74AHCT244N 3.3-to-5 V buffer | U1.10 (GND) | U1.1 (1OE_N) | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W055 | SN74AHCT244N 3.3-to-5 V buffer | U1.10 (GND) | U1.19 (2OE_N) | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W056 | DC motor contactor | TB_GND.BUS | K1.A2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W057 | Coil suppression network | K1.A2 | Z_COIL.A2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W058 | ECHO lower resistor | ESP1.GND | R24.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W059 | ECHO lower resistor | ESP1.GND | R26.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W060 | ECHO lower resistor | ESP1.GND | R28.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W061 | L_FWD input pull-down | U1.10 (GND) | R1.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W062 | L_REV input pull-down | U1.10 (GND) | R2.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W063 | R_FWD input pull-down | U1.10 (GND) | R3.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W064 | R_REV input pull-down | U1.10 (GND) | R4.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W065 | ENABLE input pull-down | U1.10 (GND) | R5.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W066 | TF input pull-down | U1.10 (GND) | R6.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W067 | TL input pull-down | U1.10 (GND) | R7.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W068 | TR input pull-down | U1.10 (GND) | R8.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W069 | BRUSH_IN1 pull-down | DRV_A.GND | R9.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W070 | BRUSH_IN2 pull-down | DRV_A.GND | R10.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W071 | CONVEYOR_IN3 pull-down | DRV_A.GND | R11.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W072 | CONVEYOR_IN4 pull-down | DRV_A.GND | R12.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W073 | DRV_L.R_EN local EN pull-down | DRV_L.GND | R13.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W074 | DRV_L.L_EN local EN pull-down | DRV_L.GND | R14.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W075 | DRV_R.R_EN local EN pull-down | DRV_R.GND | R15.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W076 | DRV_R.L_EN local EN pull-down | DRV_R.GND | R16.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W077 | DRV_A.ENA local EN pull-down | DRV_A.GND | R17.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W078 | DRV_A.ENB local EN pull-down | DRV_A.GND | R18.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W079 | L_FWD receiver pull-down | DRV_L.GND | R19.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W080 | L_REV receiver pull-down | DRV_L.GND | R20.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W081 | R_FWD receiver pull-down | DRV_R.GND | R21.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W082 | R_REV receiver pull-down | DRV_R.GND | R22.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W083 | E-stop feedback pull-down | ESP1.GND | R29.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W084 | local ceramic bypass | U1.10 (GND) | C_U1.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W085 | local ceramic bypass | US_F.GND | C_F.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W086 | local ceramic bypass | US_L.GND | C_L.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W087 | local ceramic bypass | US_R.GND | C_R.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W088 | local motor-bus reservoir | DRV_L.B- | C_BL.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W089 | local motor-bus reservoir | DRV_R.B- | C_BR.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W090 | local motor-bus reservoir | DRV_A.GND | C_BA.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W091 | 5V rail 1 OVP/OCP and supervision assembly | BUCK1.OUT- | OV1.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W092 | 5V rail 2 OVP/OCP and supervision assembly | BUCK2.OUT- | OV2.GND | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W093 | Local driver-bus transient clamp | DRV_L.B- | Z_L.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W094 | Local driver-bus transient clamp | DRV_R.B- | Z_R.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W095 | Local driver-bus transient clamp | DRV_A.GND | Z_A.- | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W096 | SN74LVC3G34DCU ECHO isolation | ESP1.GND | U2.4 (GND) | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W097 | local ceramic bypass | U2.4 (GND) | C_U2.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W098 | ECHO output default-low | ESP1.GND | R30.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W099 | ECHO output default-low | ESP1.GND | R31.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W100 | ECHO output default-low | ESP1.GND | R32.2 | ground; 0 V reference; returns sized by branch | PROVISIONAL; WIRE | Star power returns, isolated signal routing; never switch only GND | Verify actual buck common negatives; no motor return via ESP32/USB/breadboard |
| W101 | 3S high-side protection assembly | BT1.BAL_CELL0 | P1.CELL0 | sensor; Cell-stack potential; order TBD | BLOCKED_RATING; WIRE | Sense lead protection and connector order per selected P1 | No connector pin order assumed. Verify cumulative cell potentials without probing adjacent contacts with bare tips |
| W102 | 3S high-side protection assembly | BT1.BAL_CELL1 | P1.CELL1 | sensor; Cell-stack potential; order TBD | BLOCKED_RATING; WIRE | Sense lead protection and connector order per selected P1 | No connector pin order assumed. Verify cumulative cell potentials without probing adjacent contacts with bare tips |
| W103 | 3S high-side protection assembly | BT1.BAL_CELL2 | P1.CELL2 | sensor; Cell-stack potential; order TBD | BLOCKED_RATING; WIRE | Sense lead protection and connector order per selected P1 | No connector pin order assumed. Verify cumulative cell potentials without probing adjacent contacts with bare tips |
| W104 | 3S high-side protection assembly | BT1.BAL_CELL3 | P1.CELL3 | sensor; Cell-stack potential; order TBD | BLOCKED_RATING; WIRE | Sense lead protection and connector order per selected P1 | No connector pin order assumed. Verify cumulative cell potentials without probing adjacent contacts with bare tips |
| W105 | 5V rail 1 OVP/OCP and supervision assembly | FK.OUT | OV1.PG_COM | power_lc; Pack voltage; K1 coil compatibility TBD | BLOCKED_RATING; WIRE | FK + S2 coil NC | Coil must operate across actual loaded pack range, or a qualified coil supply is required |
| W106 | Momentary motor-power ARM | S2.COIL_NC | S3.COM | power_lc; Coil supply when stop released | BLOCKED_MISSING; WIRE | Independent NC E-stop chain | Pressing stop must break coil circuit even if MCU hung |
| W107 | DC motor contactor | S2.COIL_NC | K1.AUX_HOLD_COM | power_lc; Coil supply when stop released | BLOCKED_MISSING; WIRE | Independent NC E-stop chain | Pressing stop must break coil circuit even if MCU hung |
| W108 | DC motor contactor | S3.NO | K1.AUX_HOLD_NO | power_lc; Coil supply when manually latched | BLOCKED_MISSING; WIRE | Momentary S3 in parallel with K1 NO auxiliary | Verify seal-in, dropout, no automatic restart on stop release/power restoration, and clamp release time |
| W109 | DC motor contactor | S3.NO | K1.A1 | power_lc; Coil supply when manually latched | BLOCKED_MISSING; WIRE | Momentary S3 in parallel with K1 NO auxiliary | Verify seal-in, dropout, no automatic restart on stop release/power restoration, and clamp release time |
| W110 | Coil suppression network | S3.NO | Z_COIL.A1 | power_lc; Coil supply when manually latched | BLOCKED_MISSING; WIRE | Momentary S3 in parallel with K1 NO auxiliary | Verify seal-in, dropout, no automatic restart on stop release/power restoration, and clamp release time |
| W111 | ESP32-WROOM-32 DevKit | K1.AUX_SENSE_NO | ESP1.GPIO27 | control; Healthy 3.3 V; open/pressed 0 V | BLOCKED_MISSING; WIRE | Isolated NC contact, R29 pull-down; firmware internal pull-down | HIGH only when S2 released AND K1 closed. Open contact/wire or power-good loss trips; initial K1-open boot latches ESTOP until manual power-arm, RESET, ARM. |
| W112 | E-stop feedback pull-down | K1.AUX_SENSE_NO | R29.1 | control; Healthy 3.3 V; open/pressed 0 V | BLOCKED_MISSING; WIRE | Isolated NC contact, R29 pull-down; firmware internal pull-down | HIGH only when S2 released AND K1 closed. Open contact/wire or power-good loss trips; initial K1-open boot latches ESTOP until manual power-arm, RESET, ARM. |
| W113 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO16 | U1.2 (1A1) | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R1 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W114 | L_FWD input pull-down | ESP1.GPIO16 | R1.1 | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R1 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W115 | BTS7960 / IBT-2 left | U1.18 (1Y1) | DRV_L.RPWM | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W116 | L_FWD receiver pull-down | U1.18 (1Y1) | R19.1 | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W117 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO17 | U1.4 (1A2) | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R2 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W118 | L_REV input pull-down | ESP1.GPIO17 | R2.1 | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R2 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W119 | BTS7960 / IBT-2 left | U1.16 (1Y2) | DRV_L.LPWM | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W120 | L_REV receiver pull-down | U1.16 (1Y2) | R20.1 | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W121 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO18 | U1.6 (1A3) | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R3 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W122 | R_FWD input pull-down | ESP1.GPIO18 | R3.1 | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R3 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W123 | BTS7960 / IBT-2 right | U1.14 (1Y3) | DRV_R.RPWM | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W124 | R_FWD receiver pull-down | U1.14 (1Y3) | R21.1 | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W125 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO19 | U1.8 (1A4) | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R4 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W126 | R_REV input pull-down | ESP1.GPIO19 | R4.1 | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R4 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W127 | BTS7960 / IBT-2 right | U1.12 (1Y4) | DRV_R.LPWM | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W128 | R_REV receiver pull-down | U1.12 (1Y4) | R22.1 | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W129 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO14 | U1.11 (2A1) | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R5 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W130 | ENABLE input pull-down | ESP1.GPIO14 | R5.1 | control; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R5 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W131 | Latching E-stop / 3 isolated NC contacts | U1.9 (2Y1) | S2.EN_COM | control; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W132 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO32 | U1.13 (2A2) | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R6 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W133 | TF input pull-down | ESP1.GPIO32 | R6.1 | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R6 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W134 | HC-SR04 front | U1.7 (2Y2) | US_F.TRIG | sensor; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W135 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO33 | U1.15 (2A3) | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R7 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W136 | TL input pull-down | ESP1.GPIO33 | R7.1 | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R7 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W137 | HC-SR04 left | U1.5 (2Y3) | US_L.TRIG | sensor; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W138 | SN74AHCT244N 3.3-to-5 V buffer | ESP1.GPIO13 | U1.17 (2A4) | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R8 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W139 | TR input pull-down | ESP1.GPIO13 | R8.1 | sensor; 0/3.3 V | BLOCKED_MISSING; WIRE | U1 TTL-compatible input; pull-down R8 | Continuity and scope at reset/boot/brownout; do not bypass buffer without exact-board qualification |
| W140 | HC-SR04 right | U1.3 (2Y4) | US_R.TRIG | sensor; 0/5 V | BLOCKED_MISSING; WIRE | 5V non-inverting AHCT output | Verify target board accepts 5V logic; scope high/low margins and no opposing PWM |
| W141 | BTS7960 / IBT-2 left | S2.EN_NC | DRV_L.R_EN | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W142 | BTS7960 / IBT-2 left | S2.EN_NC | DRV_L.L_EN | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W143 | BTS7960 / IBT-2 right | S2.EN_NC | DRV_R.R_EN | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W144 | BTS7960 / IBT-2 right | S2.EN_NC | DRV_R.L_EN | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W145 | ONE L298N: A brushes / B conveyor | S2.EN_NC | DRV_A.ENA | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W146 | ONE L298N: A brushes / B conveyor | S2.EN_NC | DRV_A.ENB | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W147 | DRV_L.R_EN local EN pull-down | S2.EN_NC | R13.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W148 | DRV_L.L_EN local EN pull-down | S2.EN_NC | R14.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W149 | DRV_R.R_EN local EN pull-down | S2.EN_NC | R15.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W150 | DRV_R.L_EN local EN pull-down | S2.EN_NC | R16.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W151 | DRV_A.ENA local EN pull-down | S2.EN_NC | R17.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W152 | DRV_A.ENB local EN pull-down | S2.EN_NC | R18.1 | control; 0/5 V; LOW disabled | BLOCKED_MISSING; WIRE | Six local 10k pull-downs; EN jumpers removed; independent S2 NC | Calculate total input/pull load <= U1 drive and receiver VIH/VIL; no hard-HIGH module links; scope reset sequence |
| W153 | ONE L298N: A brushes / B conveyor | ESP1.GPIO21 | DRV_A.IN1 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W154 | BRUSH_IN1 pull-down | ESP1.GPIO21 | R9.1 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W155 | ONE L298N: A brushes / B conveyor | ESP1.GPIO22 | DRV_A.IN2 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W156 | BRUSH_IN2 pull-down | ESP1.GPIO22 | R10.1 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W157 | ONE L298N: A brushes / B conveyor | ESP1.GPIO23 | DRV_A.IN3 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W158 | CONVEYOR_IN3 pull-down | ESP1.GPIO23 | R11.1 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W159 | ONE L298N: A brushes / B conveyor | ESP1.GPIO25 | DRV_A.IN4 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W160 | CONVEYOR_IN4 pull-down | ESP1.GPIO25 | R12.1 | control; 0/3.3 V | PROVISIONAL; WIRE | Genuine L298 TTL input; local 10k pull-down | Verify exact module input circuit, common GND and inputs LOW at reset; IN2/IN4 held LOW by firmware |
| W161 | ECHO upper resistor | US_F.ECHO | R23.1 | sensor; Standard module: potentially 0/5 V | BLOCKED_MISSING; WIRE | 2.2k upper / 3.3k lower 1% divider required | Keep actual ECHO disconnected until parts fitted and high/low/overshoot verified independently of ESP32 |
| W162 | ECHO lower resistor | R23.2 | R24.1 | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W163 | SN74LVC3G34DCU ECHO isolation | R23.2 | U2.1 (1A) | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W164 | ESP32-WROOM-32 DevKit | U2.7 (1Y) | ESP1.GPIO34 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W165 | ECHO output default-low | U2.7 (1Y) | R30.1 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W166 | ECHO upper resistor | US_L.ECHO | R25.1 | sensor; Standard module: potentially 0/5 V | BLOCKED_MISSING; WIRE | 2.2k upper / 3.3k lower 1% divider required | Keep actual ECHO disconnected until parts fitted and high/low/overshoot verified independently of ESP32 |
| W167 | ECHO lower resistor | R25.2 | R26.1 | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W168 | SN74LVC3G34DCU ECHO isolation | R25.2 | U2.3 (2A) | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W169 | ESP32-WROOM-32 DevKit | U2.5 (2Y) | ESP1.GPIO35 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W170 | ECHO output default-low | U2.5 (2Y) | R31.1 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W171 | ECHO upper resistor | US_R.ECHO | R27.1 | sensor; Standard module: potentially 0/5 V | BLOCKED_MISSING; WIRE | 2.2k upper / 3.3k lower 1% divider required | Keep actual ECHO disconnected until parts fitted and high/low/overshoot verified independently of ESP32 |
| W172 | ECHO lower resistor | R27.2 | R28.1 | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W173 | SN74LVC3G34DCU ECHO isolation | R27.2 | U2.6 (3A) | sensor; Nominal 3.0 V at 5.0V ECHO | BLOCKED_MISSING; WIRE | 2.2k/3.3k 1% divider then U2 power-off isolation | At U2 input: HIGH >=2.0V, LOW <=0.8V, 0..5.5V and edge rate <=10ns/V. Measure actual sensor VOH/VOL/overshoot. |
| W174 | ESP32-WROOM-32 DevKit | U2.2 (3Y) | ESP1.GPIO36 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W175 | ECHO output default-low | U2.2 (3Y) | R32.1 | sensor; 0 / MCU-derived 3.3V; U2 off -> high impedance | BLOCKED_MISSING; WIRE | U2 Ioff supplied by ESP1.3V3; 100k output bias | Verify U2 VCC equals ESP32 VDD; output HIGH >=0.75*VDD, LOW <=0.25*VDD; no phantom MCU power with sensor rail live |
| W176 | motor 1 fuse / holder | DRV_L.M+ | FM1.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W177 | motor 2 fuse / holder | DRV_L.M+ | FM2.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W178 | left front wheel motor | DRV_L.M- | M1.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W179 | left rear wheel motor | DRV_L.M- | M2.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W180 | left front wheel motor | FM1.OUT | M1.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM1; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W181 | left rear wheel motor | FM2.OUT | M2.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM2; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W182 | motor 3 fuse / holder | DRV_R.M+ | FM3.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W183 | motor 4 fuse / holder | DRV_R.M+ | FM4.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W184 | right front wheel motor | DRV_R.M- | M3.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W185 | right rear wheel motor | DRV_R.M- | M4.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W186 | right front wheel motor | FM3.OUT | M3.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM3; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W187 | right rear wheel motor | FM4.OUT | M4.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM4; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W188 | motor 5 fuse / holder | DRV_A.OUT1 | FM5.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W189 | motor 6 fuse / holder | DRV_A.OUT1 | FM6.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W190 | brush 1 motor | DRV_A.OUT2 | M5.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W191 | brush 2 motor | DRV_A.OUT2 | M6.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W192 | brush 1 motor | FM5.OUT | M5.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM5; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W193 | brush 2 motor | FM6.OUT | M6.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM6; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W194 | motor 7 fuse / holder | DRV_A.OUT3 | FM7.IN | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W195 | conveyor motor | DRV_A.OUT4 | M7.B | motor; Bidirectional / PWM bridge output; not a supply rail | BLOCKED_RATING; WIRE | DC motor-lead fuse and rated branch/driver; recirculation diodes required | Verify motor current, polarity/direction, pigtail rating and overload coordination; no motor trial yet |
| W196 | conveyor motor | FM7.OUT | M7.A | motor; Bridge output after fuse | BLOCKED_RATING; WIRE | FM7; value/time curve TBD | One motor lead per fuse; no breadboard path. Motor voltage/direction still unverified |
| W197 | 5V rail 1 OVP/OCP and supervision assembly | BUCK1.OUT+ | OV1.IN+ | power_lc; 5V target; buck-fault voltage may approach pack | BLOCKED_MISSING; WIRE | OV1 required; never assume LM2596 is an overvoltage protector | Select actual independent output protection and supervisor; simulate abnormal voltage with electronics disconnected |
| W198 | 5V rail 2 OVP/OCP and supervision assembly | BUCK2.OUT+ | OV2.IN+ | power_lc; 5V target; buck-fault voltage may approach pack | BLOCKED_MISSING; WIRE | OV2 required; never assume LM2596 is an overvoltage protector | Select actual independent output protection and supervisor; simulate abnormal voltage with electronics disconnected |
| W199 | 5V rail 2 OVP/OCP and supervision assembly | OV1.PG_NO | OV2.PG_COM | power_lc; Coil supply; contact isolation required | BLOCKED_MISSING; WIRE | Both logic rails must be healthy before K1 can energize/hold | A missing/abnormal rail opens the coil chain; restoration alone must not re-latch K1. Select actual supervisor/interface circuitry. |
| W200 | Latching E-stop / 3 isolated NC contacts | OV2.PG_NO | S2.COIL_COM | power_lc; Coil supply; contact isolation required | BLOCKED_MISSING; WIRE | Both logic rails must be healthy before K1 can energize/hold | A missing/abnormal rail opens the coil chain; restoration alone must not re-latch K1. Select actual supervisor/interface circuitry. |
| W201 | DC motor contactor | S2.SENSE_NC | K1.AUX_SENSE_COM | control; 3.3 V only | BLOCKED_MISSING; WIRE | Separate dry K1 NO feedback contact in series with S2 NC | Map actual contact terminals; keep isolated from seal-in coil circuit. No jumper around this interlock. |

## No-connect / reserved terminal list

| Terminal | Disposition |
|---|---|
| DRV_L.R_IS | Unused diagnostics; insulate separately; no ESP32 ADC link |
| DRV_L.L_IS | Unused diagnostics; insulate separately; no ESP32 ADC link |
| DRV_R.R_IS | Unused diagnostics; insulate separately; no ESP32 ADC link |
| DRV_R.L_IS | Unused diagnostics; insulate separately; no ESP32 ADC link |
| CAM1.5V | Later phase: do not connect or power |
| CAM1.GND | Later phase: do not connect or power |
| CAM1.U0R | Later phase: do not connect or power |
| CAM1.U0T | Later phase: do not connect or power |
| ESP1.GPIO0 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO2 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO4 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO5 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO12 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO15 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO26 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.GPIO39 | Unassigned/reserved boot pin; leave external header unconnected |
| ESP1.UART0_TX_GPIO1 | Reserved for actual DevKit serial/programming circuit; no permanent external harness |
| ESP1.UART0_RX_GPIO3 | Reserved for actual DevKit serial/programming circuit; no permanent external harness |
| ESP1.EN_RESET | Onboard reset only; not motor ENABLE GPIO14 |

## Component / terminal legend

All physical connector positions are to be verified on the actual part. Generic safety assembly ports cannot be mapped until selection. Complete per-terminal voltage/status detail: `electrical/terminal_map.csv`.

| Reference | Component | Value / selection | Availability |
|---|---|---|---|
| ESP1 | ESP32-WROOM-32 DevKit | Exact module variant TBD | Existing, unverified |
| DRV_L | BTS7960 / IBT-2 left | Exact module variant TBD | Existing, unverified |
| DRV_R | BTS7960 / IBT-2 right | Exact module variant TBD | Existing, unverified |
| DRV_A | ONE L298N: A brushes / B conveyor | Exact module variant TBD | Existing, unverified |
| M1 | left front wheel motor | 12 V / 30 RPM | Existing, unverified |
| M2 | left rear wheel motor | 12 V / 30 RPM | Existing, unverified |
| M3 | right front wheel motor | 12 V / 30 RPM | Existing, unverified |
| M4 | right rear wheel motor | 12 V / 30 RPM | Existing, unverified |
| M5 | brush 1 motor | 12 V | Existing, unverified |
| M6 | brush 2 motor | 12 V | Existing, unverified |
| M7 | conveyor motor | Voltage TBD | Existing, unverified |
| US_F | HC-SR04 front | Exact module variant TBD | Existing, unverified |
| US_L | HC-SR04 left | Exact module variant TBD | Existing, unverified |
| US_R | HC-SR04 right | Exact module variant TBD | Existing, unverified |
| BUCK1 | LM2596 #1 | 5.0 V target | Existing, unverified |
| BUCK2 | LM2596 #2 | 5.0 V target | Existing, unverified |
| BT1 | 3S LiPo / connector | 11.1 V nominal / 3300 mAh | Existing, unverified |
| CAM1 | ESP32-CAM - later phase | Exact module variant TBD | Existing, unverified |
| P1 | 3S high-side protection assembly | SELECT PART | **Additional / missing or unselected** |
| S0 | Master load isolator | DC rating TBD | **Additional / missing or unselected** |
| S2 | Latching E-stop / 3 isolated NC contacts | SELECT PART | **Additional / missing or unselected** |
| S3 | Momentary motor-power ARM | NO; rating TBD | **Additional / missing or unselected** |
| K1 | DC motor contactor | CONTACT / COIL TBD | **Additional / missing or unselected** |
| Z_COIL | Coil suppression network | SELECT FOR K1 | **Additional / missing or unselected** |
| F0 | main pack fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FL | left driver fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FR | right driver fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FA | auxiliary driver fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| F1 | MCU buck input fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| F2 | logic buck input fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FK | contactor coil fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM1 | motor 1 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM2 | motor 2 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM3 | motor 3 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM4 | motor 4 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM5 | motor 5 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM6 | motor 6 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| FM7 | motor 7 fuse / holder | DC A / interrupt rating TBD | **Additional / missing or unselected** |
| U1 | SN74AHCT244N 3.3-to-5 V buffer | SN74AHCT244N | **Additional / missing or unselected** |
| R23 | ECHO upper resistor | 2.2k 1%, >=1/8 W | **Additional / missing or unselected** |
| R24 | ECHO lower resistor | 3.3k 1%, >=1/8 W | **Additional / missing or unselected** |
| R25 | ECHO upper resistor | 2.2k 1%, >=1/8 W | **Additional / missing or unselected** |
| R26 | ECHO lower resistor | 3.3k 1%, >=1/8 W | **Additional / missing or unselected** |
| R27 | ECHO upper resistor | 2.2k 1%, >=1/8 W | **Additional / missing or unselected** |
| R28 | ECHO lower resistor | 3.3k 1%, >=1/8 W | **Additional / missing or unselected** |
| R1 | L_FWD input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R2 | L_REV input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R3 | R_FWD input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R4 | R_REV input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R5 | ENABLE input pull-down | 2.2k 1%, >=1/8 W | **Additional / missing or unselected** |
| R6 | TF input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R7 | TL input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R8 | TR input pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R9 | BRUSH_IN1 pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R10 | BRUSH_IN2 pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R11 | CONVEYOR_IN3 pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R12 | CONVEYOR_IN4 pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R13 | DRV_L.R_EN local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R14 | DRV_L.L_EN local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R15 | DRV_R.R_EN local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R16 | DRV_R.L_EN local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R17 | DRV_A.ENA local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R18 | DRV_A.ENB local EN pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R19 | L_FWD receiver pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R20 | L_REV receiver pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R21 | R_FWD receiver pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R22 | R_REV receiver pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| R29 | E-stop feedback pull-down | 10k 1%, >=1/8 W | **Additional / missing or unselected** |
| C_U1 | local ceramic bypass | 100nF, >=10V | **Additional / missing or unselected** |
| C_F | local ceramic bypass | 100nF, >=10V | **Additional / missing or unselected** |
| C_L | local ceramic bypass | 100nF, >=10V | **Additional / missing or unselected** |
| C_R | local ceramic bypass | 100nF, >=10V | **Additional / missing or unselected** |
| C_BL | local motor-bus reservoir | C / ESR / voltage TBD | **Additional / missing or unselected** |
| C_BR | local motor-bus reservoir | C / ESR / voltage TBD | **Additional / missing or unselected** |
| C_BA | local motor-bus reservoir | C / ESR / voltage TBD | **Additional / missing or unselected** |
| OV1 | 5V rail 1 OVP/OCP and supervision assembly | SELECT / VERIFY | **Additional / missing or unselected** |
| OV2 | 5V rail 2 OVP/OCP and supervision assembly | SELECT / VERIFY | **Additional / missing or unselected** |
| TB_GND | Common ground distribution | Conductor / terminal rating TBD | **Additional / missing or unselected** |
| TB_POS | Protected positive distribution | Conductor / terminal rating TBD | **Additional / missing or unselected** |
| Z_L | Local driver-bus transient clamp | Standoff / clamp / energy TBD | **Additional / missing or unselected** |
| Z_R | Local driver-bus transient clamp | Standoff / clamp / energy TBD | **Additional / missing or unselected** |
| Z_A | Local driver-bus transient clamp | Standoff / clamp / energy TBD | **Additional / missing or unselected** |
| U2 | SN74LVC3G34DCU ECHO isolation | SN74LVC3G34DCU | **Additional / missing or unselected** |
| C_U2 | local ceramic bypass | 100nF, >=10V | **Additional / missing or unselected** |
| R30 | ECHO output default-low | 100k 1%, >=1/8 W | **Additional / missing or unselected** |
| R31 | ECHO output default-low | 100k 1%, >=1/8 W | **Additional / missing or unselected** |
| R32 | ECHO output default-low | 100k 1%, >=1/8 W | **Additional / missing or unselected** |
