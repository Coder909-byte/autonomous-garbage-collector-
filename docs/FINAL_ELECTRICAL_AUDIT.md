Historical E1 audit (2 November 2026), retained for traceability. Current design and verdict: [ENGINEERING_REVIEW_E2.md](ENGINEERING_REVIEW_E2.md) / [FINAL_GO_NO_GO.md](FINAL_GO_NO_GO.md). E2 adds ECHO isolation and regenerates every connection/export; counts and row IDs in this historical record describe E1 only.

# Final electrical audit — independent re-check of E1

**Review date:** 2 November 2026. **Reviewed revision:** `965183c9296b510f3991b449facb4350bde7e987`, electrical E1. **Overall verdict: HOLD — not ready for complete physical assembly or powered rover operation.**

**Correction follow-up — 2 November 2026:** F01, F02 and F03 are now **CLOSED for the documented drawing/export defects**. See [§11](#11-correction-follow-up--f01f03-closed) for exact changes and validation. The observations and FAIL evidence below are retained as the historical independent review. **All H01–H11 and physical assembly HOLD conditions remain open.** No physical compatibility or safety qualification has been inferred from these corrections.

The proposed functional topology is coherent and the GPIO map matches the firmware. No demonstrably wrong endpoint was found among the 188 canonical connection rows. That does **not** establish a complete, electrically qualified circuit: important blocks are unspecified functional requirements, several interfaces are missing, and no physical measurement exists. Two drawing/documentation defects in E1 and one subsequently observed working-PDF integrity defect are recorded as FAIL below. None is evidence that the canonical netlist already contains a short circuit.

This is a fresh desk review of the evidence, including an independent connectivity reconstruction, manufacturer data and independently rendered SVGs. It is not an external engineer's physical inspection or safety certification. No hardware was powered, firmware uploaded, physical serial port opened or motor command executed during this review. The reviewer did not change working firmware, GPIO assignments, electrical source, diagrams or commissioning instructions; corrections are **proposed**, not applied. On resuming after interruption, the working combined PDF was observed to differ from the initially clean reviewed commit; that change is preserved and assessed as F03.

## 1. Evidence and status definitions

- **PASS:** the stated, limited property is supported by the available evidence. A functional-net PASS is not permission to connect hardware.
- **FAIL:** an observable contradiction or incorrect assembly instruction exists. Exact locations and proposed corrections are given below.
- **HOLD:** missing part, specification, measurement or qualification prevents a conclusion. Missing information is not converted into a guessed rating.

| Evidence layer | Verdict | What was actually established |
| --- | --- | --- |
| Software verification | PASS within tested scope | Fresh builds of both ESP32 environments; 79 C++ and 21 Python tests; source/Wokwi pin agreement. Host adapter tests use stubs, not real GPIO waveforms. |
| Functional schematic/net model | PASS for external topology; HOLD for implementations | 82 represented components, 69 nets, 257 connected terminals plus 19 NC/reserved terminals; all 188 connection rows checked. Generic P1/OV1/OV2 and actual module internals remain unverified. |
| Diagram/export consistency | FAIL in F01/F02; current PDF also F03 | All 12 SVGs inspected structurally and visually; all 276 terminal labels agree with the model. F01/F02 escape the export checker; the later working-PDF corruption is recoverable by that reader. |
| Electrical compatibility and protection | HOLD | Conditional calculations and identified-chip requirements are available; actual assemblies, motor loads, protection parts and power sequencing are unqualified. |
| Wokwi runtime | Owner-reported functional pass | Existing report covers startup, ranging, movement, avoidance, cleaning and stop latching. No new runtime or quantitative trace was generated for this audit. |
| Physical hardware | HOLD / UNTESTED | No continuity, voltage, current, temperature, stopping or fault measurements have been performed. |

Inspected: `electrical/design.json`, every row of `connections.csv` and `bom.csv`, `docs/FINAL_WIRING.md`, `ELECTRICAL_BLOCKERS.md`, `ASSEMBLY_GUIDE.md`, all twelve electrical SVGs, `include/rover_pins.h`, `include/rover_control.h`, `firmware/rover.ino`, PlatformIO configuration, Wokwi sources and the relevant checker/generator/test code. Appendix A gives an individual disposition for every connection.

Fresh checks, run without upload:

| Check | Result |
| --- | --- |
| `pio test -e native` | 79/79 PASS |
| `python3 -m unittest discover -s test -p 'test_*.py' -v` | 21/21 PASS: 10 waveform-checker and 11 electrical-model tests |
| `pio run -e esp32dev -e wokwi_compile` | Both PASS; 22,232 bytes RAM and 281,345 bytes flash per build |
| `python3 scripts/check_project.py` | PASS; 16 unique GPIO assignments, generated sketch agreement, resistor-free Wokwi |
| `scripts/check_design_exports.py` using the project virtual environment | PASS; CSV/SVG/PDF structural agreement, including the 21-page PDF |
| Independent graph reconstruction, separate from project checker | PASS; all 188 row endpoints, 69 connected net graphs, BOM coverage and 276 SVG terminal labels checked |

These tests establish neither component authenticity nor electrical behavior. In particular, matching generated artifacts can repeat the same design assumption.

## 2. Independently checked component requirements

The following sources were opened afresh. Chip documentation does not identify an unknown DevKit, IBT-2 board, L298N carrier, buck module, motor or battery.

| Source | Requirement or limit used in this review |
| --- | --- |
| [Espressif ESP32-WROOM-32 v3.8](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf), pin definitions and Tables 13–14 | Module supply is 3.0–3.6 V; this is distinct from a DevKit's qualified 5 V input. Input HIGH minimum is 0.75×VDD, LOW maximum 0.25×VDD; the specified input range depends on the I/O supply. Raw 5 V ECHO is not a supported interface. |
| [Espressif ESP32 Series v5.3](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf), boot configuration and IO_MUX appendix | GPIO34/35/36 are suitable input-only choices. Used outputs avoid boot straps, flash and UART0. GPIO14/MTMS is output-disabled during reset and has an after-reset JTAG pull-up; software LOW begins later. No JTAG use is permissible on the assigned pins. |
| [TI SN74AHCT244 Rev O](https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf), pin table and recommended conditions | The proposed non-inverting 20-pin map is correct. VCC 4.5–5.5 V, VIH ≥2 V, VIL ≤0.8 V; recommended output current magnitude is 8 mA per output. OE pins 1/19 LOW enable the two groups. C_U1 is correctly proposed locally. |
| [TI SN74HC244](https://www.ti.com/lit/ds/symlink/sn74hc244.pdf), input requirements | HC and AHCT thresholds differ. Do not substitute HC for U1 or approve direct ESP32 drive merely because an IBT-2 is advertised as logic-compatible. |
| [Infineon BTS7960 Rev 1.1](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf), §§4.1, 4.3, 4.4 | Each IC is a half bridge; an IBT-2 uses a bridge assembly. Silicon operating supply is 5.5–27.5 V; IN/INH thresholds and protection apply to the IC, not an unknown module buffer. The advertised 43 A is not an approved module continuous-current rating or motor-overload setting. |
| [ST L298 DS0218 Rev 5](https://www.st.com/resource/en/datasheet/l298.pdf), Tables 1/4/5 and §5 | Logic supply 4.5–7 V; input HIGH ≥2.3 V supports qualified 3.3 V control. DC 2 A/channel is an absolute maximum, not a carrier rating. At 2 A the maximum bridge drop is 4.9 V under stated conditions. Equal inputs with EN HIGH brake; EN LOW releases the bridge. Required bypassing, flyback paths and current sensing must be verified on the carrier. |
| [TI LM2596 Rev G](https://www.ti.com/lit/ds/symlink/lm2596.pdf), application/thermal guidance | A 3 A regulator IC does not qualify an unknown assembled module's inductor, diode, capacitors, cooling or continuous output. Its protection features do not establish independent output overvoltage or 3S cell protection. |
| [HC-SR04 reference hosted by SparkFun, attributed to ElecFreaks](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf) | Typical 5 V module, ≥10 µs trigger, recommended measurement cycle >60 ms. This is not an identification/datasheet match for the owner's sensors and does not certify their ECHO VOH/VOL or power-off behavior. |

No exact motor, pack, board-regulator, contactor, fuse or protection-assembly datasheet has been supplied. Battery 12.6 V maximum is the calculation `3×4.2 V` **conditional on conventional 3S chemistry**; verify the actual label. Capacity 3.3 Ah does not give a discharge-current rating without a verified C rating and operating conditions.

## 3. GPIO and firmware cross-check

All sixteen application GPIOs are unique and correct for the declared WROOM-32 target. Actual header location is still HOLD until the particular board is identified. GPIO numbers are not header position numbers.

| GPIO | Function and proposed physical route | Canonical connection IDs | Verdict |
| --- | --- | --- | --- |
| 16 | Left FWD → U1 input 2/output 18 → left RPWM | W106–W109 | PASS mapping; HOLD interface |
| 17 | Left REV → U1 4/16 → left LPWM | W110–W113 | PASS mapping; HOLD interface |
| 18 | Right FWD → U1 6/14 → right RPWM | W114–W117 | PASS mapping; HOLD interface |
| 19 | Right REV → U1 8/12 → right LPWM | W118–W121 | PASS mapping; HOLD interface |
| 14 | Shared EN → U1 11/9 → S2 EN NC → all six EN terminals | W122–W124, W134–W145 | PASS grouping/polarity; HOLD reset/loading |
| 32 | Front trigger → U1 13/7 | W125–W127 | PASS mapping; HOLD hardware |
| 34 | Front ECHO through R23/R24 | W154–W156, W056 | PASS input-only mapping; real connection blocked |
| 33 | Left trigger → U1 15/5 | W128–W130 | PASS mapping; HOLD hardware |
| 35 | Left ECHO through R25/R26 | W157–W159, W057 | PASS input-only mapping; real connection blocked |
| 13 | Right trigger → U1 17/3 | W131–W133 | PASS mapping; HOLD hardware |
| 36 / VP | Right ECHO through R27/R28 | W160–W162, W058 | PASS input-only mapping; real connection blocked |
| 21 | Brush IN1, L298 channel A | W146–W147 | PASS mapping; HOLD carrier qualification |
| 22 | Brush IN2, held LOW | W148–W149 | PASS mapping; HOLD carrier qualification |
| 23 | Conveyor IN3, L298 channel B | W150–W151 | PASS mapping; HOLD carrier qualification |
| 25 | Conveyor IN4, held LOW | W152–W153 | PASS mapping; HOLD carrier qualification |
| 27 | Healthy feedback from isolated S2 NC + K1 sense NO | W035, W104–W105, W081, W188 | PASS fail-low intent; HOLD actual contacts |

Firmware findings:

- `firmware/rover.ino:39–65` maps forward to left/right FWD PWM, left turn to left REV/right FWD, and right turn to left FWD/right REV. Four channels use 1.2 kHz/8-bit LEDC. Drive duty is 150/255; turn duty 140/255. These are requested electrical directions, not proof of physical rotation.
- `include/rover_control.h:190–203` enforces 100 ms disabled neutral time before new motion. This does not establish zero rotor speed or zero reversal current.
- `firmware/rover.ino:53–61` and controller output gating allow auxiliary operation only while armed, healthy and actually moving forward. Independent requests do not provide independent EN pins or speed control. An unrequested auxiliary channel is electrically braked while the shared EN is HIGH.
- `firmware/rover.ino:84–107` drives outputs disabled after setup begins. GPIO27 uses an internal pull-down and disconnected feedback latches ESTOP. K1-open physical boot is therefore intentionally different from a Wokwi switch set healthy. RESET does not arm; ARM does not request movement.
- `firmware/rover.ino:16–24` clears GPIO14 in the falling-edge ISR; the main loop retains the trip latch. It does not switch K1's coil. Serial STOP/ESTOP also do not remove the motor supply.
- Sensor pulses are 10 µs. One sensor is triggered every nominal 65 ms, so a particular sensor is normally revisited about every 195 ms. The 25 ms blocking ECHO wait delays serial processing; 500 ms freshness is not a physical stopping-time guarantee. Three sensors can still cross-talk or return plausible false ranges.
- Turning uses 180 ms settling, 100 ms output neutral time, up to 540 ms enabled-turn timing, post-stop fresh readings from all three sensors, 35/45 cm entry/recovery hysteresis and at most three unsuccessful attempts. The time starts from adapter-applied software output, not an encoder measurement.
- Invalid/stale ranges disarm **AUTO**. Manual movement retains its 1.2 s timeout but is not protected by automatic obstacle avoidance. There is no current, jam, cell-voltage or real speed feedback, and no external AUTO heartbeat.
- A CPU reset starts software disarmed but does not necessarily drop K1: OV1 monitors a 5 V rail, not the MCU's execution or necessarily its 3.3 V supply. A brownout can precede a clean reset. Safe real enable behavior remains H03/H07, not a software PASS.

## 4. Subsystem verdicts

PASS in the topology column means the intended external net relationship is coherent. It does not qualify the unknown internal circuitry of a module or functional protection block.

| Subsystem | Topology / software | Electrical / physical verdict | Missing evidence or correction |
| --- | --- | --- | --- |
| ESP32 application GPIO map | PASS | HOLD | H01 actual DevKit header/regulator identification |
| Four wheel PWM and polarity interlock | PASS | HOLD | H03 receiver levels; H05 rotation/reversal current |
| Both BTS R_EN and L_EN pins | PASS, all four included | HOLD | H03 remove hard-HIGH links and qualify enable behavior |
| Left BTS with M1/M2 parallel | PASS topology | HOLD | H05 summed load/start/stall and board thermal limits |
| Right BTS with M3/M4 parallel | PASS topology | HOLD | H05 equivalent measurements on this separate board/pair |
| BTS power-return overview | FAIL documentation F01 | HOLD | Explicit B- heavy return; verify GND/B- internal bond |
| One L298 IN1–IN4 and ENA/ENB | PASS grouping and genuine-IC logic thresholds | HOLD | H01/H03/H06 regulator, links, diodes, bypassing and input load |
| Both brushes on channel A | PASS parallel topology | HOLD | H06 combined starting/running/jam/braking current and simultaneous heat |
| Conveyor on channel B | PASS separate command path | HOLD | H06 motor voltage, torque, loaded current and transport direction |
| U1 non-inverting channel map | PASS identified-part pinout | HOLD | H03 part missing, real loading and supply/reset waveforms |
| GPIO14 default-low network | PASS proposed bias topology | HOLD | H03 R5 and local pulls missing; actual after-reset/brownout levels |
| Pin-chart electrical status | FAIL documentation F02 | HOLD | Missing-interface rows must retain BLOCKED_MISSING status |
| Three TRIG paths | PASS proposed 5 V buffered topology | HOLD | H02/H03 actual pulse levels, module requirements and interference |
| Three ECHO dividers | PASS proposed divider topology | HOLD; keep unplugged | H02 parts missing; real high/low/overshoot and power-off isolation |
| Common ground routing | PASS functional graph | HOLD | H04 board bonds, conductor capacity, voltage drop and noise |
| Both buck input/output paths | PASS; positive outputs separate | HOLD | H07 actual conversion/load/ripple and fault response |
| ESP32 5 V/VIN and USB | PASS separation intent | HOLD | H01/H07 board-approved input and measured backfeed behavior |
| Battery positive distribution | PASS functional routing | HOLD | H08 actual P1, polarity, pack ratings and protected distribution |
| Battery negative distribution | PASS high-side-protection concept | HOLD | H04/H08 actual BMS topology and no unintended bypass |
| Main/branch/motor fuses | PASS locations as a proposal | HOLD | H08/H10 fourteen actual fuse selections/curves/interrupt ratings |
| Balance/cell-sense leads | PASS named potential correspondence only | HOLD | H08 actual pin order and short protection; these bypass F0/S0 |
| Motor reservoirs/clamps | PASS local placement after branch fuses | HOLD | H10 capacitance/ESR/voltage/clamp energy and recirculation |
| K1 main cutoff path | PASS series position upstream of all three motor supplies | HOLD | H09 actual DC contacts, coil range, release, residual bus energy and backfeed |
| Coil PG/stop/seal-in chain | PASS functional relay logic | HOLD | H07/H09 selected isolated contacts, dropout and restart behavior |
| Separate stop feedback and EN contacts | PASS isolation intent and fail-low software | HOLD | H03/H09 low-current contact suitability, physical isolation and faults |
| Reverse-polarity / accidental shorts | No automatic reverse-input protection demonstrated | HOLD | H08 keyed connectors or qualified protection, routing, mounts and fuse coordination |
| Jam/overload protection | No firmware detection; fuse provisions only | HOLD | H05/H06/H10 protection must act before motor/driver/lead damage |
| Seven-motor simultaneous operation | Command topology supports it in forward mode | HOLD | H05/H06/H07/H08/H10 complete current, voltage-drop, heat and fault budget |
| Autonomous physical movement and collection | PASS simulated/control intent | HOLD | H11 traction, inertia, sensor placement, sweep/transport and stop tests |
| Reserved ESP32-CAM | PASS no-connect disposition | HOLD for any later use | No supply/current budget, harness or GPIO allocation approved |
| Current combined PDF integrity | FAIL F03; reviewed Git version is intact | Not an electrical measurement | Recoverable page text does not close damaged cross-reference offsets; validate a binary-correct replacement candidate |

## 5. FAIL findings — corrections proposed after completing the audit

### F01 — BTS overview does not identify the required power-return terminal

**FAIL category: assembly-drawing clarity/consistency, not canonical net connectivity.**

- **Exact location:** `docs/diagrams/motor_drivers.svg:12` and `:29`; equivalent text appears in `motor_drivers.pdf` and the combined package. Source: `scripts/generate_wiring.py:218`.
- **Related connections:** W043/W045 are the dedicated `TB_GND → DRV_L.B- / DRV_R.B-` returns. W044/W046 are **INTERNAL_VERIFY** relationships between each board's B- and logic GND; they are not replacement external motor-return wires.
- **Problem:** each BTS overview says `GND -> power return` and omits B-. Because GND is also a named logic-header terminal on the represented board, this is ambiguous as a physical instruction and contradicts the more precise return routing in the CSV and assembly guide. Following the shorthand could route motor return through a logic-header lead.
- **Required correction:** explicitly label `B- → TB_GND, dedicated branch-rated power return`; separately state `logic GND internally bonded to B-: verify actual board, no thin duplicate motor return`. Preserve W043–W046 and all firmware GPIOs. Regenerate the affected overview exports only after the generator correction is reviewed.
- **Limit:** the canonical B- connections already exist and are coherent. The review does not allege an existing assembled wrong return; no hardware is connected.

### F02 — pin chart does not preserve missing-hardware status

**FAIL category: release-status consistency.**

- **Exact location:** `docs/diagrams/esp32_pinout.svg`, GPIO16/17/18/19/14/32/33/13/27 rows, electrical-status column; for example line 18 labels GPIO16 `PROVISIONAL`. Equivalent PDF and combined-package rows inherit this. Source: `scripts/generate_wiring.py`, `pinout()`, where all non-ECHO rows receive the same literal status.
- **Related connections:** W104–W145 and W188 as applicable to these signal chains. The relevant GPIO nets in `electrical/design.json` and their rows in `connections.csv` are **BLOCKED_MISSING** because U1, required bias/interface parts or cutoff feedback hardware are missing.
- **Problem:** the chart downgrades the explicit blocker to `PROVISIONAL`, despite describing the column as electrical status. The distinction is defined in FINAL_WIRING.md and matters before assembly. Its global HOLD banner prevents this from being an overall approval, but does not make the row labels consistent.
- **Required correction:** derive each chart status from its actual net and the full endpoint chain. Display at least BLOCKED_MISSING for those nine routes, with concise missing-part notes. Keep ECHO blocked and preserve every GPIO number. Do not reclassify a route merely because a GPIO itself is valid.

### F03 — working combined PDF has damaged binary-header bytes

**FAIL category: current delivered-file integrity; not an electrical net error and not present in the reviewed committed PDF.**

- **Exact file:** `docs/diagrams/electrical_package.pdf`, bytes 10–21 in the working file. **Connection IDs:** none individually; this is the combined export containing the complete connection table, W001–W188.
- **Observed difference:** the original four binary marker bytes `E2 E3 CF D3` following `%PDF-1.4` have become four UTF-8 replacement characters, twelve bytes total. The eight-byte increase invalidates the stored cross-reference offsets. The PDF reader warns `incorrect startxref pointer` and recovers by parsing objects.
- **Strict check:** `PdfReader(..., strict=True)` accepts the committed 21-page PDF but rejects the working file with `PdfReadError: Broken xref table`. The existing export checker uses the reader's recovery mode and does not catch this integrity failure.
- **Evidence:** reviewed committed PDF is 65,902 bytes, SHA-256 `40ed126984d22d6192a158737423dc87ed17f5fd325d230990dc74da47d86d3e`; current working PDF is 65,910 bytes, SHA-256 `61e35bfbadc071358c7cdea01e0cb433b6baba9a5e57b194d40aee6fae4f9364`. Both recover 21 pages with identical extracted page text and no annotations. Recovery does not make the file byte-correct or guarantee all viewers/print workflows.
- **Required correction:** recover a byte-exact copy of the reviewed export, or regenerate from the reviewed source, in a separate candidate file; validate its cross-reference integrity and contents before replacing the working file. Handle PDF as binary throughout; the existing `.gitattributes` already marks it binary. Do not repair it by text decoding/re-encoding.
- **Disposition:** this differing working file appeared after the initial review checks. It was not overwritten or silently restored. The responsible application/process was not established. SVG/net-model conclusions are unaffected.

No proven wrong external net endpoint, directly shorted supply or overlapping firmware GPIO was found in E1. Unknown module pin order, unknown currents and absent components are HOLD findings, not fabricated FAIL measurements.

## 6. HOLD register — information/components needed

All rows below are open. Existing blocker IDs refer to [ELECTRICAL_BLOCKERS.md](ELECTRICAL_BLOCKERS.md).

| Review ID | Missing information / component | Required closure evidence | Existing blockers |
| --- | --- | --- | --- |
| H01 | Exact DevKit, both IBT-2 boards, L298 carrier and connector identities | Manufacturer/schematic or traced actual silkscreen-to-function mapping; DevKit 5 V/USB path; L298 regulator link, sense termination, bypass and diode identities; qualify genuine input behavior | B01, B13 |
| H02 | ECHO conditioning, actual sensor output behavior and powered-off input protection | Fit/qualify R23–R28 or reviewed alternative; measure VCC, trigger, raw/divided VOH/VOL, pulse/noise/overshoot against actual MCU VDD; prove no unsafe back-powering during independent rail loss | B02, B09, B13 |
| H03 | U1, default-low networks, enable loading and reset behavior | Obtain exact AHCT part and R1–R22/R29/bypass parts as required by E1; remove conflicting links/pull-ups; measure all EN/PWM/input levels during startup/reset/brownout/rail faults with motors unavailable | B03, B04 |
| H04 | Return-path construction and capacity | Check W040/042/044/046 internal bonds; qualify dedicated heavy returns, logic returns, connectors, ground drop/noise, heatsink/tab/mount isolation; no breadboard/Dupont motor paths | B01, B11, B12 |
| H05 | Individual wheel-motor and wheel-pair electrical ratings | All four rated voltages/tolerances; operating/start/stall demand and durations; module/heatsink/terminal limits for each summed side; current-limited, guarded direction/reversal and thermal evidence | B05, B07 |
| H06 | Brush/conveyor requirements and shared L298 load capability | Individual and summed running/start/jam **and braking** currents; conveyor voltage; shared package, diodes, cooling and terminal budget; adequate delivered torque/voltage and inward/transport directions | B05, B06, B12 |
| H07 | Buck assemblies and real OV1/OV2 implementations | Two independent regulated outputs, measured load/ripple/transients; selected OVP/OCP/window supervision and fail-open isolated PG contacts; fault let-through, thresholds, sequencing, MCU 3.3 V behavior and USB isolation | B09, B13 |
| H08 | Pack identity and real battery-side protection/distribution | Chemistry/C rating/condition/maker cell limits; actual compatible high-side P1; balance connector order and sense-lead protection; keyed/polarity strategy, adjacent main fuse, wire/connector ratings and suitable charging arrangement | B10, B11 |
| H09 | Real independent cutoff hardware and fault coverage | DC-rated K1 main contacts/coil/two NO auxiliaries; S0, three-isolated-NC S2, S3, coil clamp and PG interfaces; actual terminal mapping/wetting/isolation; release/restart/backfeed/residual-energy and guarded stop tests | B08, B09, B14 |
| H10 | Coordinated overload and transient protection | Select F0/FL/FR/FA/F1/F2/FK/FM1–FM7 and conductors from measured demand and fault current; prove time-current/I²t and motor/semiconductor protection; qualify C_BL/BR/BA, Z_L/R/A and inductive fuse opening | B11, B12 |
| H11 | Real sensing/mechanics and complete commissioning | Physical acoustic crosstalk, target coverage and plausible false readings; traction, turn/stopping distances, brush sweep, conveyor direction/torque, debris/jam behavior and sustained seven-motor load acceptance | B14 |

### ECHO and independent supply loss require particular attention

The divider is correctly oriented: 2.2 kΩ upper series resistor and 3.3 kΩ lower to MCU ground. With an assumed 5.0 V ECHO HIGH, the calculated output is `5×3.3/(2.2+3.3) = 3.0 V`. Combining 1% resistor extremes with an **assumed** ECHO HIGH equal to a 4.75–5.25 V rail gives approximately 2.827–3.175 V. These are calculations, not sensor measurements. Actual output drive/sag and MCU supply limits must also satisfy the interface.

The model powers the MCU and sensors from different protected rails: W023 versus W028–W030. If the MCU supply fails while sensor power persists, a HIGH ECHO can still reach the divider and MCU input through W154–W162. OV1/OV2 PG contacts open the **K1 coil chain**, not those ECHO wires or sensor power. The design therefore has not established a power-off-safe GPIO interface. Normal startup sequencing instructions alone do not cover an unexpected rail failure. Resolve this with a reviewed power-off-safe conditioning or supply/sequencing implementation and qualification; do not assume series resistance makes unspecified injection current acceptable. U1's valid-powered specifications are likewise not a blanket guarantee for every partial-power condition.

### Shared enable fanout and the L298 braking case

The six proposed 10 kΩ enable pull-downs draw `6×5/10000 = 3.0 mA` nominally, or approximately 3.182 mA at 5.25 V with 1% low resistance, **before** actual module input currents and pull-ups. This fits within U1's stated output-drive envelope only if the additional loading and required VOH/VOL margins are qualified. R5's 2.2 kΩ bias counters GPIO14's after-reset pull-up, but no measured reset/brownout waveform exists. An internal pull resistance's typical value is not a worst-case startup guarantee. Opening S2 EN relies on the local receiver pulls and removal of conflicting hard-HIGH links. H03 stays open.

With wheels moving forward and shared EN HIGH, `BRUSH OFF` makes IN1=IN2=LOW, while `CONVEYOR OFF` makes IN3=IN4=LOW. This actively brakes the respective L298 channel; it does not independently disconnect it. A spinning load can produce a significant braking current. H06 must cover two parallel brushes stopping together, a conveyor being switched off during travel, and simultaneous package heating. Do not qualify only steady running current.

For the brush channel, use `I_A = I_M5 + I_M6`; for the conveyor, `I_B = I_M7`. An illustrative loss bound at the cited 2 A/drop test point is `2 A × 4.9 V = 9.8 W` for **one bridge**, before other losses. This is not an allowable operating point or a prediction of the owner's module. Both bridges share the thermal package. If qualification fails, the shared L298 arrangement must be revised; passing software cannot correct an overloaded power stage.

### Power, overload and emergency cutoff limitations

- Each wheel side is one parallel motor load. Neither driver provides individual wheel speed/jam control. Use summed starting and overload demand, with the bus and pack sized for the credible simultaneous case. PWM duty is not a motor or wire rating.
- F0 is appropriately proposed adjacent to pack positive; branch fuses precede drivers/bucks and individual motor fuses are proposed in A leads. Fourteen fuse locations are accounted for. Values, DC interruption, wire coordination and inductive breaking behavior remain undefined. A fuse protecting a cable may act too slowly to protect an L298 or motor. Electronic limiting/tripping is required **if** manufacturer limits and coordinated fuse behavior cannot otherwise meet the overload envelope; do not add a sensor merely to conceal this missing analysis.
- The four balance-sense leads W094–W097 remain connected independently of S0 and F0. A sense-lead short can bypass main-load protection. Actual lead protection and connect/disconnect sequence must come from the selected pack/protector arrangement, not functional labels alone.
- No explicit qualified reverse-battery protection is demonstrated. P1's stated UV/OV/OCP function must not be assumed to include it. Keyed connectors, polarity checks and any required reverse-current/reverse-input function must be resolved. A fuse does not inherently prevent reverse-voltage damage.
- Local clamps remain on each driver's side of its branch fuse, a sound proposed placement. Opening K1/P1 or a fuse can leave capacitance and motor-generated energy downstream. Verify clamp/recirculation paths and decay; an open supply contact does not prove zero bus voltage or immediate mechanical stopping.
- Pressing physical S2 opens the EN contact and coil chain independently of the CPU. With correctly selected healthy parts, K1 then removes the pack source from all three motor supplies. Actual hardware is missing, so this is a functional conclusion, not a demonstrated stop. Serial ESTOP does not open K1. Logic remains separately powered; real modules must be checked for unintended backfeed.
- The seal-in circuit provides normal no-auto-restart only with S3 released and contacts functioning. Held/stuck S3, welded K1/S2 contacts, shorted feedback, delayed release and failed supervision are not diagnosed by this single-channel design. K1 sense feedback is not verified mirror-contact evidence of the main contacts. No safety category, fault tolerance or emergency-stop performance is certified.
- No motor current may pass through the available breadboards, jumper leads, ESP32 or USB/PC return. No bridge output may be treated as permanent ground. Probe switching motor outputs only with appropriately rated differential/isolated measurement methods; a grounded scope clip can short a bridge.

## 7. Scenario assessment A–M

Every physical scenario remains HOLD. The support column describes the proposal and current code, not observed hardware behavior.

| Scenario | Expected electrical behavior / proposal support | Failure modes and missing protection | Required physical evidence |
| --- | --- | --- | --- |
| A. ESP32 powers on | Software disarmed, PWM/cleaning requests zero; K1 normally open; disconnected/open K1 feedback latches ESTOP | GPIO14 before setup, rail ramp, pull-ups, unpowered I/O and USB backfeed are unqualified | Isolated USB-only boot first; later scope every driver EN across qualified rail ramps/reset. H01–H03/H07/H09 |
| B. Rover is armed | Hardware power-ARM closes K1 only through PG/S2; healthy feedback permits RESET then ARM; serial ARM alone requests no movement | Incorrect auxiliary contact mapping, stuck S3, stale HIGH EN, unselected PG or jumpers can defeat intended behavior | Motor loads absent: actual contact/feedback truth table, EN LOW, no motion request on RESET/ARM, deliberate restart sequence. H03/H09 |
| C. Four wheels forward | After neutral time, left RPWM and right RPWM PWM; both LPWM LOW, both half-bridge enables on each side HIGH; paired motors share outputs | One reversed motor, excessive summed current, droop, hot board/connector or unequal load | Each motor first, then raised-wheel paired rotation/current/temperature and reversal tests. H04/H05/H08/H10 |
| D. Left turn | Left LPWM PWM/right RPWM PWM, opposite inputs LOW; cleaning disabled; bounded turn then stopped reassessment | Physical orientation may invert direction; skid friction and residual rotation can create high current; no rear sensing | Measured direction, interlock timing, loaded turn current, clearance and stopping. H03/H05/H11 |
| E. Right turn | Left RPWM PWM/right LPWM PWM; otherwise same protections as left | Same risks on opposite mechanical/power paths | Independent mirrored physical test; not inferred from left-turn pass. H03/H05/H11 |
| F. Obstacle detected | AUTO requests stop/settle, selects a clear side, turns, then uses new readings; invalid/stale ranges disarm | False plausible echoes/crosstalk, 65 ms sensor staggering, blocked ECHO hardware, inertia and limited field of view | Qualified sensor voltages first; measured physical update/stop latency and target coverage. H02/H03/H11 |
| G. Both brushes inward | Both share OUT1/OUT2 through individual fuses while armed forward; lead orientation must be mapped to inward sweep | One brush can spin outward, pair current overloads A, mutual generator currents and OFF braking unqualified | Each guarded brush, correct lead mapping, pair running/start/jam/braking and thermal test. H06/H10/H11 |
| H. Conveyor transports waste | IN3 HIGH/IN4 LOW only on a forward request; OUT3/OUT4 supplies M7 independently of brush request | Unknown motor voltage/direction, insufficient voltage after bridge loss, high start/jam/braking current | Rating identification, guarded individual electrical test, then loaded transport/heat. H06/H10/H11 |
| I. All seven motors run | Possible in forward mode with CLEAN ON; wheel PWM and auxiliary on/off channels share pack demand | Battery C limit, wiring drop, BMS/contact/fuse limits, buck resets and common L298 heating remain unbudgeted | Credible simultaneous start and sustained loaded current/voltage/thermal records after individual gates pass. H04–H10 |
| J. Emergency stop | Physical S2 opens EN and K1 coil; software trips from feedback; release alone normally cannot restore dropped seal-in | Contact/coil ratings, release time, welding, held S3, stored/regenerated energy and backfeed unverified; serial stop alone leaves supply live | Logic-only independent cutoff test first; later guarded loaded interruption, residual voltage/stopping time and restart tests. H03/H09/H10/H11 |
| K. ESP32 resets | Software state lost → disarmed; proposed pulls keep EN LOW through reset. K1 may remain closed | MCU reset/brownout does not necessarily drop 5 V PG; JTAG/default states or rail imbalance may produce unsafe levels | Scope actual EN/PWM, feedback, 3.3/5 V and K1 through reset/brownout; verify no restart. H03/H07/H09 |
| L. Battery sags | Selected P1 should disconnect on maker-specific cell UV; PG/coil should drop when relevant rails fail | Unknown thresholds/response, cell imbalance, contactor chatter, GPIO backfeed and regenerated voltage | Controlled isolated source/cell simulation, individual-cell limits, sequencing, dropout/no-restart and thermal records; do not deep-discharge pack. H02/H07–H10 |
| M. Motor jams | Current rises; only properly coordinated protection can interrupt/limit it. Firmware has no jam detection | A single small motor or L298 can fail before main/branch fuse opens; BTS chip current limit may be much too high for the load | Manufacturer overload curves or safely current-limited fixture characterization; demonstrate trip/limiting before damage. H05/H06/H08/H10 |

## 8. Actual diagram review

All SVGs were parsed and rendered with an SVG renderer independent of the generator; this was not a review of generator success messages or PNG previews alone. The full six-sheet schematic accounts for every modeled terminal once. Symbols for unknown assemblies describe functional ports, not purchasable pinouts.

| SVG | Visual/structural finding |
| --- | --- |
| `complete_schematic_01.svg` | Battery/cell sense, F0/S0/P1, distribution, S2/S3/K1, PG assemblies and local clamps are represented with net labels. Generic blocks remain implementation HOLD. |
| `complete_schematic_02.svg` | Two buck supplies and the remaining supply fuses represented; OUT+ rails distinct; black negative nets common. Internal negative bonds require measurement. |
| `complete_schematic_03.svg` | ESP32, U1, both BTS modules, L298 and front/left sensors match canonical signal nets. All six driver enable terminals are included. |
| `complete_schematic_04.svg` | Right sensor, all seven motors, seven lead fuses, front divider and reserved camera represented. Motor outputs remain separate from ground. |
| `complete_schematic_05.svg` | Remaining dividers and first input/enable pull-downs correctly connect their named signal nodes to ground. Values are proposed parts, not inventory. |
| `complete_schematic_06.svg` | Remaining pulls, bypass capacitors and three bus reservoirs represented. Reservoir ratings remain TBD; no circuit simulation or physical layout qualification. |
| `sensor_wiring.svg` | Three independent dividers, correct upper/lower orientation, junction dots and ground branches; correct trigger-buffer channels and GPIOs. H02 remains unresolved. |
| `esp32_pinout.svg` | GPIO/endpoint numbers correct; no guessed header orientation. **FAIL F02** for nine status labels. |
| `motor_drivers.svg` | Parallel load groups, motor-output names and control channels correct. **FAIL F01** in BTS return-terminal labeling. Orange lines explicitly represent two-conductor bundles. |
| `power_distribution.svg` | Proposed pack/contactor/branch/buck topology agrees with model. Return paths are summarized by a note, not drawn as a complete negative harness. Use canonical return rows; this overview alone is insufficient to assemble. |
| `emergency_stop.svg` | Coil seal-in, separate 3.3 V feedback and gated EN agree with the model. Low-current isolated contacts and generic hardware remain HOLD; no certified safety circuit implied. |
| `physical_wiring.svg` | Placement/bundle sketch, not terminal orientation. Left/right/auxiliary bundles and reserved camera clear; full individual power/return/signal wiring still requires the CSV and schematic. Some power/signal routes cross; colors/labels and the stated non-junction convention must be retained. |

Red supply, black ground, blue control, green sensor and orange motor conventions are used. Branch T joins on block overviews and sensor junction dots have identifiable roles; unrelated crossings are not electrical connections. For a later assembly release, add bridge/junction markings wherever an actual harness drawing could be misread, and show explicit negative return conductors. These are clarity improvements, not evidence that crossing strokes have shorted the netlist.

The existing checker verifies label/graph/PDF coverage. It does **not** verify the prose of F01, propagate F02 statuses, prove buffer power-off behavior, check contact/fuse ratings, model internal module circuitry or evaluate motor thermal behavior. A passing result cannot close those items.

## 9. Missing components, measurements and proposed next corrections

**Mandatory functions before the affected physical circuit is released:** qualified sensor voltage interfaces; safe default-low driver controls with compatible logic; actual regulated/overvoltage/overcurrent-protected supplies; battery-specific cell protection; suitable DC cutoff/manual restart hardware; coordinated fusing, wiring/connectors and suppression. E1's concrete proposed additions include U1, R1–R29, local bypass parts, fourteen fuses/holders, distribution, S0/S2/S3/K1, selected P1/OV1/OV2 implementations, coil suppression, reservoirs and clamps. These are not demonstrated to be owned or fitted. Generic blocks may need multiple actual components.

Do not buy another motor driver solely because measurements are missing. First establish whether the actual existing wheel stages and the shared L298 satisfy the load and fault envelope. Likewise, verified board-integrated pulls, diodes or protection can count toward a requirement only after they are identified and the design is explicitly revised. Optional later improvements include encoders, current telemetry, battery telemetry, improved localization and the camera. Such optional features do not substitute for mandatory hardware protection; a qualifying overload function may become mandatory if passive coordination is inadequate.

Corrections proposed **after** this review:

1. Correct F01/F02 in the generator and associated exports, and repair the separately preserved F03 PDF candidate after validating its provenance/integrity; extend semantic checks for the exact BTS return-terminal text and pin-chart blocker propagation. No GPIO change is needed.
2. Close H01 and select actual implementations for P1/OV1/OV2/K1/S2/S3 before treating their functional port labels as wiring instructions. Reconsider complexity only through an explicit reviewed revision retaining every required protection function.
3. Resolve H02/H03/H07 for independent rail loss, valid-powered and unpowered interfaces, shared enable fanout and default states. Obtain missing interface parts; never install raw ECHO or hard-HIGH enable bypasses.
4. Resolve H05/H06/H08/H10 from real ratings and appropriately controlled measurements. Include auxiliary braking, pair stall/start demand, voltage loss, sustained heat and protection clearing time. Revise a driver stage only if this evidence shows it unsuitable.
5. Complete H09 independent cutoff qualification before any energy-bearing motor commissioning. Use [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md) only with its stage gates, corrected drawings and measured acceptance limits.
6. Advance to guarded drivetrain/cleaning/navigation tests only after earlier gates pass. Preserve the existing disabled boot, ARM, latching stop, neutral interval, manual timeout and AUTO sensor protection.

No design correction, firmware change, commit or GitHub push is performed by this audit. Only this requested audit report and local ignored evidence are added.

## 10. Explicit answers to the ten final questions

| Question | Answer |
| --- | --- |
| 1. Is the circuit logically correct? | **The external functional topology is coherent, conditionally.** No wrong canonical endpoint found. It is not a verified complete implementable circuit while generic protection blocks and exact module internals are unspecified. F01/F02 must also be corrected; F03 affects the current combined PDF. |
| 2. Are the GPIO connections correct? | **PASS for firmware-to-functional-net mapping:** all 16 are unique and appropriate to the declared WROOM-32. Actual DevKit terminal positions and voltage-qualified interfaces remain HOLD. |
| 3. Can two BTS7960 drivers control four wheel motors? | **Yes as two parallel side groups in principle, not four independent channels.** Actual suitability is HOLD until each side's summed demands and actual board ratings/heat are qualified. |
| 4. Can one L298N safely drive both brushes and conveyor? | **Not established.** Topology is possible, but combined A-channel load, B load, braking and shared thermal/diode capacity are unknown. Do not connect that load until H06 passes. |
| 5. Is the ESP32 protected from unsafe voltage? | **Not yet demonstrated.** Proposed divider/buffer/supply protections are missing or unselected; real ECHO stays disconnected. Independent rail-loss/back-power behavior remains unresolved. |
| 6. Is the battery power system safe? | **Not established; HOLD.** Pack limits, actual P1, sense-lead protection, polarity strategy, fuses, conductors, connectors and transient/charging behavior are unqualified. |
| 7. Will emergency stop actually remove motor power? | **Physical S2/K1 topology can remove the pack source independently of software if implemented and qualified correctly. No actual cutoff exists in the confirmed inventory/evidence.** Serial STOP/ESTOP does not remove supply voltage; residual/regenerated energy and real contact/backfeed behavior must be measured. |
| 8. What components are missing? | The mandatory interface/protection/cutoff/distribution parts listed in §9 and the BOM; implementation/ratings are still needed for the generic blocks. Existing board-level substitutes are unverified. |
| 9. What measurements are required? | H01–H11: pin mapping/continuity; raw/divided signal and reset/rail-fault waveforms; loading/backfeed; per-motor and summed running/start/stall/braking currents; loaded voltages, temperature, cell sag; fuse/cutoff/transient response; physical direction, sensing and stopping performance. No values have been invented. |
| 10. Is the rover READY FOR PHYSICAL ASSEMBLY? | **NO for the complete rover or powered assembly. Release remains HOLD.** Identification, labeling and separately gated bare-ESP32 USB work can be prepared under their explicit isolation conditions; that is not release of the motor/battery/sensor harness. |

## 11. Correction follow-up — F01–F03 closed

Only diagram/export generation, validation, regression coverage and verification documentation changed. Electrical topology, all 188 connection records, the BOM/terminal map, all 16 GPIOs, canonical firmware, Wokwi sketch/circuit and PlatformIO configuration are byte-for-byte unchanged against the pre-correction snapshot. No new ground wire or internal module bond was introduced.

| Finding | Implemented correction | Closure evidence |
| --- | --- | --- |
| F01 — ambiguous BTS return label | Both BTS overview cards now explicitly say `B- -> TB_GND; dedicated branch-rated power return`, with a separate `GND/B- internal bond: VERIFY; no extra return wire` instruction. Updated generator and SVG/PDF/PNG exports, including the combined PDF. | Semantic checks inspect the visible text in each BTS card and its PDF export. W043/W045 retain heavy B- returns; W044/W046 remain INTERNAL_VERIFY. Ground-route guards reject conversion of a verification row into a new wire. |
| F02 — understated pin-chart status | Row status derives from the most restrictive canonical status across the depicted signal route, including buffer output, shared enable, raw ECHO and feedback nets as applicable. Nine previously understated routes now show BLOCKED_MISSING. The three ECHO routes also show BLOCKED_MISSING with explicit disconnected notes; four L298 input rows remain PROVISIONAL with HOLD notes. | All 16 visible row labels checked against the model in SVG and individual/combined PDF. Regression rejects downgrading a buffer or ECHO row, and verifies a downstream blocker cannot disappear when the upstream status differs. |
| F03 — damaged PDF offsets | Regenerated binary PDF from corrected sources. Merged PDFs are written to a temporary candidate, validated and atomically replace the destination only on success. The original damaged working PDF is preserved under ignored `artifacts/audit-corrections/electrical_package.damaged.pdf`. | Strict pypdf parsing, classic startxref **and every in-use object offset**, and page text extraction pass for all 15 PDFs. Combined PDF remains 21 pages. Regressions reproduce the original text-reencoding corruption and stale object offsets even after adjusting startxref. |

Corrected combined PDF SHA-256: `591275a5ca91cdf4c76f4fc225f2489bf1871fa48603e4ab3311b2825327f80e`. Its electrical release is **HOLD**. Generated overview labels were also visually inspected using a renderer independent of the generator. Unrelated schematic SVGs and the complete physical-harness SVG retain their original connectivity.

Validation after corrections: **79 C++ + 31 Python = 110 tests PASS**, including all original 100 tests and 10 new export regressions. Both ESP32 builds PASS. The electrical-model, source/Wokwi, complete 188-row graph, 276-terminal SVG and strict 15-PDF export checks PASS. No new Wokwi runtime was executed; owner-reported simulation and physical UNTESTED status remain distinct. No upload, real serial command, battery connection or motor activation occurred.

Reproduction:

```sh
.venv/bin/python scripts/generate_wiring.py
.venv/bin/python scripts/check_design_exports.py
python3 scripts/verify.py
```

Logs: `artifacts/design-export-checks.log`, `artifacts/verification-run.log`, `artifacts/python-tests.log`, `artifacts/native-tests.log` and `artifacts/build.log`. Local before/after source hashes and damaged-file evidence are under ignored `artifacts/audit-corrections/`. See [ELECTRICAL_BLOCKERS.md](ELECTRICAL_BLOCKERS.md#practical-completion-essentials) for the essential components/specifications/measurements and optional improvements. Closing F01–F03 does not close any physical blocker.

## Appendix A. Individual connection dispositions

Each row below was compared with the canonical net, endpoint existence, generated schematic labels and its intended subsystem behavior. **PASS here means functional routing agreement only. Every physical row remains HOLD**, including rows originally called PROVISIONAL. Actual terminal mapping H01 applies throughout. `INTERNAL_VERIFY` means check the board's existing bond; do not fit an extra jumper from this row. F01/F02 references identify affected drawing discrepancies, not failed canonical copper connections. F03 concerns the whole working combined PDF rather than one endpoint.

| ID | Source → destination | Net | Row kind | Functional routing | Physical verdict / open findings |
| --- | --- | --- | --- | --- | --- |
| W001 | `BT1.PACK+` → `F0.IN` | `PACK_RAW` | WIRE | PASS within stated scope | HOLD: H08, H10 |
| W002 | `F0.OUT` → `S0.COM` | `PACK_FUSED` | WIRE | PASS within stated scope | HOLD: H08, H10 |
| W003 | `S0.OUT` → `P1.IN+` | `PACK_ISOLATED` | WIRE | PASS within stated scope | HOLD: H08, H10 |
| W004 | `TB_POS.BUS` → `P1.OUT+` | `PACK_PROTECTED` | WIRE | PASS within stated scope | HOLD: H08 |
| W005 | `TB_POS.BUS` → `K1.MAIN_COM` | `PACK_PROTECTED` | WIRE | PASS within stated scope | HOLD: H08, H09 |
| W006 | `TB_POS.BUS` → `F1.IN` | `PACK_PROTECTED` | WIRE | PASS within stated scope | HOLD: H07, H08, H10 |
| W007 | `TB_POS.BUS` → `F2.IN` | `PACK_PROTECTED` | WIRE | PASS within stated scope | HOLD: H07, H08, H10 |
| W008 | `TB_POS.BUS` → `FK.IN` | `PACK_PROTECTED` | WIRE | PASS within stated scope | HOLD: H07, H08, H10 |
| W009 | `K1.MAIN_NO` → `FL.IN` | `MOTOR_SWITCHED` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W010 | `K1.MAIN_NO` → `FR.IN` | `MOTOR_SWITCHED` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W011 | `K1.MAIN_NO` → `FA.IN` | `MOTOR_SWITCHED` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W012 | `FL.OUT` → `DRV_L.B+` | `LEFT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W013 | `FL.OUT` → `C_BL.+` | `LEFT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W014 | `FL.OUT` → `Z_L.+` | `LEFT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W015 | `FR.OUT` → `DRV_R.B+` | `RIGHT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W016 | `FR.OUT` → `C_BR.+` | `RIGHT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W017 | `FR.OUT` → `Z_R.+` | `RIGHT_SUPPLY` | WIRE | PASS within stated scope | HOLD: H05, H09, H10 |
| W018 | `FA.OUT` → `DRV_A.Vs_12V` | `AUX_SUPPLY` | WIRE | PASS within stated scope | HOLD: H06, H09, H10 |
| W019 | `FA.OUT` → `C_BA.+` | `AUX_SUPPLY` | WIRE | PASS within stated scope | HOLD: H06, H09, H10 |
| W020 | `FA.OUT` → `Z_A.+` | `AUX_SUPPLY` | WIRE | PASS within stated scope | HOLD: H06, H09, H10 |
| W021 | `F1.OUT` → `BUCK1.IN+` | `MCU_BUCK_IN` | WIRE | PASS within stated scope | HOLD: H07, H10 |
| W022 | `F2.OUT` → `BUCK2.IN+` | `LOGIC_BUCK_IN` | WIRE | PASS within stated scope | HOLD: H07, H10 |
| W023 | `OV1.OUT+` → `ESP1.5V_VIN` | `V5_MCU` | WIRE | PASS within stated scope | HOLD: H01, H07 |
| W024 | `OV2.OUT+` → `U1.20` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W025 | `OV2.OUT+` → `DRV_L.VCC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W026 | `OV2.OUT+` → `DRV_R.VCC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W027 | `OV2.OUT+` → `DRV_A.5V_LOGIC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W028 | `OV2.OUT+` → `US_F.VCC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W029 | `OV2.OUT+` → `US_L.VCC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W030 | `OV2.OUT+` → `US_R.VCC` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W031 | `OV2.OUT+` → `C_U1.1` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W032 | `OV2.OUT+` → `C_F.1` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W033 | `OV2.OUT+` → `C_L.1` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W034 | `OV2.OUT+` → `C_R.1` | `V5_LOGIC` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W035 | `ESP1.3V3` → `S2.SENSE_COM` | `V3V3` | WIRE | PASS within stated scope | HOLD: H03, H09 |
| W036 | `TB_GND.BUS` → `BT1.PACK-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H08 |
| W037 | `TB_GND.BUS` → `P1.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H08 |
| W038 | `BUCK1.OUT-` → `ESP1.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H07 |
| W039 | `TB_GND.BUS` → `BUCK1.IN-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H07 |
| W040 | `BUCK1.IN-` → `BUCK1.OUT-` | `GND` | INTERNAL_VERIFY | PASS within stated scope | HOLD: H04, H07 |
| W041 | `TB_GND.BUS` → `BUCK2.IN-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H07 |
| W042 | `BUCK2.IN-` → `BUCK2.OUT-` | `GND` | INTERNAL_VERIFY | PASS within stated scope | HOLD: H04, H07 |
| W043 | `TB_GND.BUS` → `DRV_L.B-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H05, F01 |
| W044 | `DRV_L.B-` → `DRV_L.GND` | `GND` | INTERNAL_VERIFY | PASS within stated scope | HOLD: H04, H05, F01 |
| W045 | `TB_GND.BUS` → `DRV_R.B-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H05, F01 |
| W046 | `DRV_R.B-` → `DRV_R.GND` | `GND` | INTERNAL_VERIFY | PASS within stated scope | HOLD: H04, H05, F01 |
| W047 | `TB_GND.BUS` → `DRV_A.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H06 |
| W048 | `BUCK2.OUT-` → `US_F.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W049 | `BUCK2.OUT-` → `US_L.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W050 | `BUCK2.OUT-` → `US_R.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W051 | `BUCK2.OUT-` → `U1.10` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W052 | `U1.10` → `U1.1` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W053 | `U1.10` → `U1.19` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W054 | `TB_GND.BUS` → `K1.A2` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H09 |
| W055 | `K1.A2` → `Z_COIL.A2` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H09 |
| W056 | `ESP1.GND` → `R24.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W057 | `ESP1.GND` → `R26.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W058 | `ESP1.GND` → `R28.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H04 |
| W059 | `U1.10` → `R1.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W060 | `U1.10` → `R2.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W061 | `U1.10` → `R3.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W062 | `U1.10` → `R4.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W063 | `U1.10` → `R5.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W064 | `U1.10` → `R6.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W065 | `U1.10` → `R7.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W066 | `U1.10` → `R8.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W067 | `DRV_A.GND` → `R9.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04, H06 |
| W068 | `DRV_A.GND` → `R10.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04, H06 |
| W069 | `DRV_A.GND` → `R11.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04, H06 |
| W070 | `DRV_A.GND` → `R12.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04, H06 |
| W071 | `DRV_L.GND` → `R13.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W072 | `DRV_L.GND` → `R14.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W073 | `DRV_R.GND` → `R15.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W074 | `DRV_R.GND` → `R16.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W075 | `DRV_A.GND` → `R17.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W076 | `DRV_A.GND` → `R18.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W077 | `DRV_L.GND` → `R19.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W078 | `DRV_L.GND` → `R20.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W079 | `DRV_R.GND` → `R21.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W080 | `DRV_R.GND` → `R22.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H04 |
| W081 | `ESP1.GND` → `R29.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H09 |
| W082 | `U1.10` → `C_U1.2` | `GND` | WIRE | PASS within stated scope | HOLD: H03, H07 |
| W083 | `US_F.GND` → `C_F.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W084 | `US_L.GND` → `C_L.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W085 | `US_R.GND` → `C_R.2` | `GND` | WIRE | PASS within stated scope | HOLD: H02, H07 |
| W086 | `DRV_L.B-` → `C_BL.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W087 | `DRV_R.B-` → `C_BR.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W088 | `DRV_A.GND` → `C_BA.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W089 | `BUCK1.OUT-` → `OV1.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H07 |
| W090 | `BUCK2.OUT-` → `OV2.GND` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H07 |
| W091 | `DRV_L.B-` → `Z_L.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W092 | `DRV_R.B-` → `Z_R.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W093 | `DRV_A.GND` → `Z_A.-` | `GND` | WIRE | PASS within stated scope | HOLD: H04, H10 |
| W094 | `BT1.BAL_CELL0` → `P1.CELL0` | `CELL0` | WIRE | PASS within stated scope | HOLD: H08 |
| W095 | `BT1.BAL_CELL1` → `P1.CELL1` | `CELL1` | WIRE | PASS within stated scope | HOLD: H08 |
| W096 | `BT1.BAL_CELL2` → `P1.CELL2` | `CELL2` | WIRE | PASS within stated scope | HOLD: H08 |
| W097 | `BT1.BAL_CELL3` → `P1.CELL3` | `CELL3` | WIRE | PASS within stated scope | HOLD: H08 |
| W098 | `FK.OUT` → `OV1.PG_COM` | `COIL_FUSED` | WIRE | PASS within stated scope | HOLD: H09 |
| W099 | `S2.COIL_NC` → `S3.COM` | `COIL_STOP_CHAIN` | WIRE | PASS within stated scope | HOLD: H09 |
| W100 | `S2.COIL_NC` → `K1.AUX_HOLD_COM` | `COIL_STOP_CHAIN` | WIRE | PASS within stated scope | HOLD: H09 |
| W101 | `S3.NO` → `K1.AUX_HOLD_NO` | `COIL_HOLD` | WIRE | PASS within stated scope | HOLD: H09 |
| W102 | `S3.NO` → `K1.A1` | `COIL_HOLD` | WIRE | PASS within stated scope | HOLD: H09 |
| W103 | `S3.NO` → `Z_COIL.A1` | `COIL_HOLD` | WIRE | PASS within stated scope | HOLD: H09 |
| W104 | `K1.AUX_SENSE_NO` → `ESP1.GPIO27` | `ESTOP_OK` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W105 | `K1.AUX_SENSE_NO` → `R29.1` | `ESTOP_OK` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W106 | `ESP1.GPIO16` → `U1.2` | `L_FWD_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W107 | `ESP1.GPIO16` → `R1.1` | `L_FWD_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W108 | `U1.18` → `DRV_L.RPWM` | `L_FWD_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W109 | `U1.18` → `R19.1` | `L_FWD_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W110 | `ESP1.GPIO17` → `U1.4` | `L_REV_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W111 | `ESP1.GPIO17` → `R2.1` | `L_REV_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W112 | `U1.16` → `DRV_L.LPWM` | `L_REV_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W113 | `U1.16` → `R20.1` | `L_REV_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W114 | `ESP1.GPIO18` → `U1.6` | `R_FWD_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W115 | `ESP1.GPIO18` → `R3.1` | `R_FWD_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W116 | `U1.14` → `DRV_R.RPWM` | `R_FWD_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W117 | `U1.14` → `R21.1` | `R_FWD_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W118 | `ESP1.GPIO19` → `U1.8` | `R_REV_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W119 | `ESP1.GPIO19` → `R4.1` | `R_REV_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W120 | `U1.12` → `DRV_R.LPWM` | `R_REV_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W121 | `U1.12` → `R22.1` | `R_REV_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W122 | `ESP1.GPIO14` → `U1.11` | `ENABLE_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W123 | `ESP1.GPIO14` → `R5.1` | `ENABLE_3V3` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W124 | `U1.9` → `S2.EN_COM` | `ENABLE_5V` | WIRE | PASS within stated scope | HOLD: H03, F02 |
| W125 | `ESP1.GPIO32` → `U1.13` | `TF_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W126 | `ESP1.GPIO32` → `R6.1` | `TF_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W127 | `U1.7` → `US_F.TRIG` | `TF_5V` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W128 | `ESP1.GPIO33` → `U1.15` | `TL_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W129 | `ESP1.GPIO33` → `R7.1` | `TL_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W130 | `U1.5` → `US_L.TRIG` | `TL_5V` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W131 | `ESP1.GPIO13` → `U1.17` | `TR_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W132 | `ESP1.GPIO13` → `R8.1` | `TR_3V3` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W133 | `U1.3` → `US_R.TRIG` | `TR_5V` | WIRE | PASS within stated scope | HOLD: H02, H03, F02 |
| W134 | `S2.EN_NC` → `DRV_L.R_EN` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W135 | `S2.EN_NC` → `DRV_L.L_EN` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W136 | `S2.EN_NC` → `DRV_R.R_EN` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W137 | `S2.EN_NC` → `DRV_R.L_EN` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W138 | `S2.EN_NC` → `DRV_A.ENA` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W139 | `S2.EN_NC` → `DRV_A.ENB` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W140 | `S2.EN_NC` → `R13.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W141 | `S2.EN_NC` → `R14.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W142 | `S2.EN_NC` → `R15.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W143 | `S2.EN_NC` → `R16.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W144 | `S2.EN_NC` → `R17.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W145 | `S2.EN_NC` → `R18.1` | `EN_DRIVER_5V` | WIRE | PASS within stated scope | HOLD: H03, H09, F02 |
| W146 | `ESP1.GPIO21` → `DRV_A.IN1` | `BRUSH_IN1` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W147 | `ESP1.GPIO21` → `R9.1` | `BRUSH_IN1` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W148 | `ESP1.GPIO22` → `DRV_A.IN2` | `BRUSH_IN2` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W149 | `ESP1.GPIO22` → `R10.1` | `BRUSH_IN2` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W150 | `ESP1.GPIO23` → `DRV_A.IN3` | `CONVEYOR_IN3` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W151 | `ESP1.GPIO23` → `R11.1` | `CONVEYOR_IN3` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W152 | `ESP1.GPIO25` → `DRV_A.IN4` | `CONVEYOR_IN4` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W153 | `ESP1.GPIO25` → `R12.1` | `CONVEYOR_IN4` | WIRE | PASS within stated scope | HOLD: H01, H03, H06 |
| W154 | `US_F.ECHO` → `R23.1` | `EF_RAW` | WIRE | PASS within stated scope | HOLD: H02 |
| W155 | `R23.2` → `R24.1` | `EF_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W156 | `R23.2` → `ESP1.GPIO34` | `EF_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W157 | `US_L.ECHO` → `R25.1` | `EL_RAW` | WIRE | PASS within stated scope | HOLD: H02 |
| W158 | `R25.2` → `R26.1` | `EL_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W159 | `R25.2` → `ESP1.GPIO35` | `EL_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W160 | `US_R.ECHO` → `R27.1` | `ER_RAW` | WIRE | PASS within stated scope | HOLD: H02 |
| W161 | `R27.2` → `R28.1` | `ER_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W162 | `R27.2` → `ESP1.GPIO36` | `ER_SAFE` | WIRE | PASS within stated scope | HOLD: H02 |
| W163 | `DRV_L.M+` → `FM1.IN` | `DRV_L_MP` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W164 | `DRV_L.M+` → `FM2.IN` | `DRV_L_MP` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W165 | `DRV_L.M-` → `M1.B` | `DRV_L_MN` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W166 | `DRV_L.M-` → `M2.B` | `DRV_L_MN` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W167 | `FM1.OUT` → `M1.A` | `M1_A` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W168 | `FM2.OUT` → `M2.A` | `M2_A` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W169 | `DRV_R.M+` → `FM3.IN` | `DRV_R_MP` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W170 | `DRV_R.M+` → `FM4.IN` | `DRV_R_MP` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W171 | `DRV_R.M-` → `M3.B` | `DRV_R_MN` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W172 | `DRV_R.M-` → `M4.B` | `DRV_R_MN` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W173 | `FM3.OUT` → `M3.A` | `M3_A` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W174 | `FM4.OUT` → `M4.A` | `M4_A` | WIRE | PASS within stated scope | HOLD: H05, H10 |
| W175 | `DRV_A.OUT1` → `FM5.IN` | `DRV_A_OUT1` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W176 | `DRV_A.OUT1` → `FM6.IN` | `DRV_A_OUT1` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W177 | `DRV_A.OUT2` → `M5.B` | `DRV_A_OUT2` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W178 | `DRV_A.OUT2` → `M6.B` | `DRV_A_OUT2` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W179 | `FM5.OUT` → `M5.A` | `M5_A` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W180 | `FM6.OUT` → `M6.A` | `M6_A` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W181 | `DRV_A.OUT3` → `FM7.IN` | `DRV_A_OUT3` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W182 | `DRV_A.OUT4` → `M7.B` | `DRV_A_OUT4` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W183 | `FM7.OUT` → `M7.A` | `M7_A` | WIRE | PASS within stated scope | HOLD: H06, H10 |
| W184 | `BUCK1.OUT+` → `OV1.IN+` | `V5_MCU_RAW` | WIRE | PASS within stated scope | HOLD: H07 |
| W185 | `BUCK2.OUT+` → `OV2.IN+` | `V5_LOGIC_RAW` | WIRE | PASS within stated scope | HOLD: H07 |
| W186 | `OV1.PG_NO` → `OV2.PG_COM` | `COIL_PG1` | WIRE | PASS within stated scope | HOLD: H07, H09 |
| W187 | `OV2.PG_NO` → `S2.COIL_COM` | `COIL_PG2` | WIRE | PASS within stated scope | HOLD: H07, H09 |
| W188 | `S2.SENSE_NC` → `K1.AUX_SENSE_COM` | `SENSE_STOP_OK` | WIRE | PASS within stated scope | HOLD: H09, F02 |

Original E1 row classifications: **42 BLOCKED_RATING, 79 BLOCKED_MISSING, 67 PROVISIONAL**. None is a physical approval. The four INTERNAL_VERIFY rows are W040, W042, W044 and W046. All 19 NC/reserved terminals were checked separately; they remain unconnected, including driver diagnostics, unused ESP32 headers and the reserved camera ports.

