# MOTOR_OPERATION: electrical conditions and exact proposed connections

18 November 2026. This is a **proposed, blocked wiring handover**, not evidence of an installed or qualified motor system. The supplied inventory includes two HW-039/IBT-2 boards with SN74HC244, one L298N, motors, LiPo, buck converters and jumper wires. It does not include the external buffer or a completed protected motor supply. Actual board photos/continuity records are absent from the repository. User-reported working USB, ultrasonic and camera integrations are preserved.

The original PROTECTED_ROVER wiring in [READY_TO_WIRE.md](READY_TO_WIRE.md) and [FINAL_GO_NO_GO.md](FINAL_GO_NO_GO.md) remains unchanged, including its physical E-stop/contactor/GPIO27 requirements. The new MOTOR_OPERATION profile does not require that GPIO27 circuit. It requires its own reviewed driver interface, fail-off behavior, protected supply and independently accessible motor-power disconnect before outputs may be released.

## What the HW-039 inputs require

The onboard SN74HC244 is a CMOS logic buffer, not galvanic isolation and not a substitute for an external AHCT voltage translator. TI specifies minimum HIGH input levels of 3.15 V at VCC=4.5 V and 4.2 V at VCC=6 V. The actual HIGH requirement depends on the measured buffer supply. A nominal 3.3 V ESP32 output does not establish the worst-case margin for a 5 V HC receiver. Do not apply the BTS7960 chip's own lower input thresholds directly to a header that feeds the HC244. [TI SN74HC244, section 5.3](https://www.ti.com/lit/ds/symlink/sn74hc244.pdf)

The module guide specifies +5 V logic power and active-HIGH R_EN/L_EN. Its general 3.3 V compatibility claim does not qualify these particular clones. Changing VCC to 3.3 V is not approved without tracing and qualifying the complete board. [Supplier guide, control header](https://www.handsontec.com/dataspecs/module/BTS7960%20Motor%20Driver.pdf)

The concrete candidate interface below is **U1 = external SN74AHCT244N, not owned**. Its TTL-compatible input limits are HIGH >=2 V and LOW <=0.8 V at its specified supply. It can translate GPIO commands to nominal 0/5 V; loaded levels, fan-out and sequencing still require qualification. [TI SN74AHCT244, sections 5.3/7.3](https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf)

## Proposed common interface: BLOCKED until fitted and qualified

The following defines actual source and destination pins rather than an unspecified conditioned signal. It is a candidate remedy, not an assertion that this alone completes power/fail-off qualification.

| Source | Destination | Levels / required physical part | Current status |
| --- | --- | --- | --- |
| Main ESP32 GPIO16 | U1 pin 2, 1A1 | 0/3.3 V; local 10 kohm input pull-down to GND | BLOCKED: U1 and pull-down absent |
| Main ESP32 GPIO17 | U1 pin 4, 1A2 | 0/3.3 V; local 10 kohm input pull-down | BLOCKED |
| Main ESP32 GPIO18 | U1 pin 6, 1A3 | 0/3.3 V; local 10 kohm input pull-down | BLOCKED |
| Main ESP32 GPIO19 | U1 pin 8, 1A4 | 0/3.3 V; local 10 kohm input pull-down | BLOCKED |
| Main ESP32 GPIO14 | U1 pin 11, 2A1 | Shared 0/3.3 V enable command; local 10 kohm pull-down | BLOCKED |
| Qualified LOGIC_5V rail | U1 pin 20 and 100 nF local bypass to pin 10 | Regulated nominal 5 V, within all receiver/interface limits | BLOCKED: rail/load/sequence qualification |
| Common signal GND | U1 pin 10 | Low-impedance logic reference; no motor current in this path | Wiring/continuity review required |
| GND | U1 pins 1 and 19, active-LOW OE | Existing candidate topology enables buffers while logic rail is valid; not an undervoltage guarantee | BLOCKED pending ramp/brownout tests; additional supervisor/gating is required if fail-off cannot be proved |
| GND | Unused U1 inputs 13, 15, 17 | Do not leave unused CMOS inputs floating | Required in this proposed motor-only interface |
| U1 outputs 7, 5, 3 | No connection | Unused outputs; leave insulated | No sensor rewiring implied |

The existing working ultrasonic interface is not routed through these unused channels. The protected E2 drawing can use those channels for its separate proposed trigger interface; this new table does not replace that drawing.

## Left HW-039: every terminal

| Module terminal | Exact source / destination | Expected signal or power | Status / dependency |
| --- | --- | --- | --- |
| VCC | Qualified LOGIC_5V rail | Nominal +5 V logic, not LiPo | BLOCKED: verify actual board supply/rail |
| GND | Common logic/signal GND at the driver reference | 0 V; verify internal GND/B- bond | Continuity and return routing required |
| RPWM | U1 pin 18, 1Y1, from GPIO16 -> U1 pin 2 | 0/5 V PWM; firmware channel 0 | BLOCKED: external U1/interface qualification |
| LPWM | U1 pin 16, 1Y2, from GPIO17 -> U1 pin 4 | 0/5 V PWM; firmware channel 1 | BLOCKED |
| R_EN | U1 pin 9, 2Y1, from GPIO14 -> U1 pin 11 | Shared nominal 0/5 V; local 10 kohm pull-down to module GND | BLOCKED: no hard-HIGH link; fan-out/fail-off qualification |
| L_EN | Same U1 pin 9 / GPIO14 path | Same shared enable, own local pull-down | BLOCKED; both enables are required |
| R_IS | Unconnected, separately insulated | Current/alarm output, not a command input | No ESP32 ADC connection or current feedback claimed |
| L_IS | Unconnected, separately insulated | Current/alarm output | Same |
| B+ | F_L output, downstream of qualified pack protection and DC motor disconnect | Actual reviewed motor-supply voltage | BLOCKED: protection, fuse/current/wire ratings |
| B- | Heavy star power-return bus | Battery/protected-supply negative reference | BLOCKED: rated wire/terminals; not MCU/USB return |
| M+ | Reviewed motor-lead fuse branches to left motor 1 A and left motor 2 A | Switched bridge output, not a supply rail | BLOCKED: parallel combined/stall currents and lead protection |
| M- | Left motor 1 B and left motor 2 B | Other switched bridge output | BLOCKED: verify physical forward polarity before release |

## Right HW-039: every terminal

| Module terminal | Exact source / destination | Expected signal or power | Status / dependency |
| --- | --- | --- | --- |
| VCC | Qualified LOGIC_5V rail | Nominal +5 V logic | BLOCKED: actual rail/board qualification |
| GND | Common logic/signal GND at driver reference | 0 V; verify internal GND/B- bond | Continuity/return review required |
| RPWM | U1 pin 14, 1Y3, from GPIO18 -> U1 pin 6 | 0/5 V PWM; channel 2 | BLOCKED: U1/interface qualification |
| LPWM | U1 pin 12, 1Y4, from GPIO19 -> U1 pin 8 | 0/5 V PWM; channel 3 | BLOCKED |
| R_EN | U1 pin 9, 2Y1, from GPIO14 -> U1 pin 11 | Shared nominal 0/5 V; local 10 kohm pull-down | BLOCKED: remove verified permanent HIGH links; qualify fan-out/fail-off |
| L_EN | Same U1 pin 9 / GPIO14 path | Same shared enable, own local pull-down | BLOCKED; both enables required |
| R_IS | Unconnected, separately insulated | Current/alarm output | No ADC/current-monitoring claim |
| L_IS | Unconnected, separately insulated | Current/alarm output | Same |
| B+ | F_R output, downstream of protected motor supply/DC disconnect | Reviewed motor-supply voltage | BLOCKED: qualified branch protection |
| B- | Heavy star power-return bus | Protected-supply negative reference | BLOCKED: rated return harness |
| M+ | Reviewed motor-lead fuse branches to right motor 1 A and right motor 2 A | Switched bridge output | BLOCKED: combined/stall currents, motor lead ratings |
| M- | Right motor 1 B and right motor 2 B | Other bridge output | BLOCKED: physical forward polarity verification |

F_L/F_R are identified branch-fuse functions, not owned/selected parts. Ratings cannot be assigned from motor RPM or the module's advertised peak current. Motor lead names A/B are functional labels; actual polarity must be identified with a controlled commissioning test. Firmware GPIO assignments do not change if a mirrored motor pair needs its physical leads reversed.

## Enable behavior and physical limits

Both R_EN/L_EN on **both** modules, plus L298N ENA/ENB, receive U1 pin 9. Six local enable pull-downs are required unless equivalent actual-board circuitry is independently verified. The known six 10 kohm pulls would draw about 3 mA at 5 V before receiver input/pull-up loads; qualify the total against U1 and actual receiver thresholds. Never tie enables permanently HIGH.

Whether a particular HW-039 has a hard-HIGH link or pull-up is **not established**: no board photos/continuity evidence are present. With all power removed, trace each enable to its HC244 input and VCC/GND, identify any resistor/zero-ohm/solder links, and document removal of permanent HIGH connections. Do not infer the two boards have identical links or cut unidentified tracks.

LOW inhibit disables each BTS half bridge in normal operation; HIGH enables its PWM-controlled switching. PWM LOW with enable HIGH can connect low-side switches, producing braking rather than electrical disconnection. Driver inhibit is not LiPo isolation; fault/overvoltage behavior also matters. [Infineon BTS7960, sections 4.4.5/4.4.6](https://www.infineon.com/dgdl/Infineon-BTS7960-DS-v01_01-en.pdf?fileId=db3a304412b407950112b43945006d5d)

| Event | Firmware expectation in MOTOR_OPERATION | Electrical qualification still required |
| --- | --- | --- |
| Boot after setup executes | GPIO14 LOW; four PWM channels zero; four auxiliary pins LOW; disarmed | Default-low receiver pins throughout rail ramps/reset, before firmware runs |
| ARM alone | Enable stays LOW; no motion/PWM request | No spurious driver input pulses |
| New direction | EN LOW and all channels zero during 100 ms neutral; selected PWM prepared before EN HIGH | Actual receiver polarity/thresholds and scope verification |
| Normal S / DISARM | EN LOW, PWM zero, auxiliary inputs LOW | Stopping distance/coasting are unmeasured |
| STOP / ESTOP | Same disabled outputs, software latch set | Battery remains connected until independent physical disconnection |
| Command loss, including AUTO | Disarm at 1200 ms valid-command deadline, evaluated in the loop | PulseIn/serial/loop overhead adds latency; no hard real-time or isolation claim |
| Reset / MCU control power missing | Software is not executing | External defaults and rail-sequence tests must keep both enables LOW; current setup is BLOCKED |
| Brownout / driver logic supply missing while motor supply lives | Firmware cannot guarantee pin or buffer states | BLOCKED until actual fail-off/backfeed/undervoltage behavior is proved or appropriate hardware gating is added |

## L298N: exact functional header mapping

| L298N terminal | Connection | Requirement / status |
| --- | --- | --- |
| IN1 | ESP32 GPIO21 | Brush forward command, 0/3.3 V; verify actual carrier feeds TTL-compatible L298 input; local 10 kohm default-low pull |
| IN2 | ESP32 GPIO22 | Held LOW by firmware; same input/default-low qualification |
| IN3 | ESP32 GPIO23 | Conveyor forward command, 0/3.3 V; same qualification |
| IN4 | ESP32 GPIO25 | Held LOW by firmware; same qualification |
| ENA | U1 pin 9 / shared GPIO14 interface | Nominal 0/5 V; remove ENA HIGH jumper; local default-low pull |
| ENB | Same U1 pin 9 / shared GPIO14 interface | Same; remove ENB HIGH jumper; local default-low pull |
| OUT1 / OUT2 | Brush motor pair, reviewed parallel branches | BLOCKED pending combined brush current, per-motor protection, connector/thermal review |
| OUT3 / OUT4 | Conveyor motor leads | BLOCKED pending its rated voltage/stall current/thermal review |
| VS, often labelled +12V | F_A output from protected/disconnectable motor-supply bus | BLOCKED: no unprotected battery jumper |
| 5V logic terminal | Qualified LOGIC_5V **only after** identifying actual regulator-jumper behavior | BLOCKED: do not parallel onboard regulator output and external 5 V; do not use this output to feed the ESP32 |
| GND | Heavy common power-return bus plus valid signal reference | No motor return through ESP32/USB/breadboard |

A genuine L298 specifies HIGH >=2.3 V and LOW <=1.5 V for inputs/enables; direct 3.3 V auxiliary signals are conditional on actual carrier circuitry and loaded MCU levels. Its package current limits do not qualify a complete module or a parallel brush pair. Verify logic supply, recirculation-diode population/ratings, heatsinking and both channels' combined dissipation. [ST L298, electrical characteristics](https://www.st.com/resource/en/datasheet/l298.pdf)

Existing cleaning behavior is preserved: BRUSH/CONVEYOR requests are independent, but applied cleaning runs only during enabled forward wheel motion. OFF sets that channel's two inputs LOW; because enable is shared, this is a commanded stop/brake state rather than an independent supply disconnect. Global S/DISARM/ESTOP drops shared EN as well.

## Power and necessary missing items

Proposed path: **LiPo positive -> correctly rated pack fuse -> qualified battery/cell/overcurrent protection -> accessible DC-rated motor-supply disconnect -> individually protected F_L/F_R/F_A branches -> driver motor-power inputs**. Negative returns use a rated heavy star bus. The actual battery chemistry/cell count, full-charge voltage, discharge limit and protection behavior must be confirmed. No fuse, switch, wire or parallel-motor rating is inferred from the current inventory.

Logic path: a separately protected branch feeds the qualified LM2596 input(s); regulated outputs feed only their assigned MCU/control loads. Adjust and measure unloaded and loaded outputs **before** connecting boards. Check buck input range, current, ripple, transients and thermal behavior. Never connect LiPo to GPIO/3V3, parallel positive buck outputs, route motor current through logic wires, or assume a generic buck can supply every load. Main DevKit USB/external-power backfeed must be resolved from its actual power path; otherwise use one verified source at a time. Preserve the independent camera supply/interface and existing working sensor wiring.

This mode needs independently disconnectable protected motor power; it does **not** assume the missing S2/contactor assembly or claim an automatic physical E-stop. A reviewed manual DC motor disconnect is a different function from GPIO27 feedback and software stop. The original protected profile still requires its own original hardware.

Smallest currently necessary remedies/evidence:

1. A qualified HC244-compatible interface, such as the explicitly mapped missing AHCT244N, with decoupling and verified input/enable default-low components. Add supply supervision/gating if the actual fail-off tests cannot pass with that interface.
2. A rated motor-power harness, branch/pack protection and accessible DC-rated disconnect; jumper wires are not a qualified high-current motor harness. Correct battery/cell protection and transient behavior must be established.
3. Actual left/right paired-motor start/stall current, brush-pair/conveyor current and L298N/IBT-2 connector/thermal data, to select protection rather than guessing ratings.
4. Scope/meter records for GPIO/header HIGH/LOW margins, boot/reset/brownout, control-power loss with motor power present, enable links/defaults, buck rails/common ground and USB backfeed. No such measurements were performed here.

Only after these conditions are physically established and reviewed may `include/rover_commissioning.h` record all six conditions true with the retained evidence identifier, followed by a new reviewed MOTOR_OPERATION build. This is a visible release attestation, **not live hardware detection**. Do not set it merely to suppress inhibition. The current source truthfully records every condition false and keeps outputs inhibited. No dashboard/serial commissioning bypass exists; the host-only qualified test fixture is rejected by ESP32/Arduino compilation.
