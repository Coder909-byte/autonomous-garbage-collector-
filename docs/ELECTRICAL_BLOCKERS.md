Current E2 update: [ENGINEERING_REVIEW_E2.md](ENGINEERING_REVIEW_E2.md) and [FINAL_PURCHASE_LIST.md](FINAL_PURCHASE_LIST.md). U2 SN74LVC3G34DCU, C_U2 and R30–32 are now explicitly modeled between dividers and GPIOs to address the independently powered ECHO path. These are additional required parts; actual waveform/rail sequencing qualification and all B01–B14 remain HOLD.

# Electrical release blockers — E1

**Physical release: HOLD.** No physical connection has been approved or measured. The circuit is fully described at the net/functional-terminal level, but the following missing parts/data prevent a final build-ready component selection. Do not substitute wire links for an unresolved protection block. Inventory parts are not presumed electrically compatible merely because their names match a drawing.

| ID | Unresolved item | What must be supplied or established | Affected work |
|---|---|---|---|
| B01 | Exact DevKit and module variants | Actual DevKit pin labels, 5V/VIN/USB schematic; both IBT-2 board buffer/supply/input ratings; L298 regulator, enable links and diode network; both buck board ratings/polarity | All module harness termination and power application |
| B02 | ECHO conditioning unavailable | Six 1% divider resistors R23–R28 (or a documented qualified alternative), exact sensor voltage behavior and measured post-divider VOH/VOL/overshoot | **All real ECHO plugs remain disconnected** |
| B03 | Logic buffer/default-low parts unavailable | U1 exact SN74AHCT244N or a separately revised validated interface; R1–R22 and R29, bypass parts; receiver load/default state checks | PWM/TRIG/enable physical interface; no bypass to GPIO or hard-HIGH enables |
| B04 | GPIO14 reset behavior | Actual reset/power-ramp/brownout EN waveforms with R5 and local receiver pulls; no driver enable glitch; no JTAG; verified module pull-ups removed | Any motor-power arming |
| B05 | Seven motor ratings/currents | Rated voltage/tolerance; running, starting and stall demand/duration at allowed supply; conveyor voltage unknown; physical direction/pigtail ratings | Driver choice, thermal design, overload limits, all power trials |
| B06 | L298 shared channel suitability | Sum of M5+M6 current on A; M7 on B; simultaneous package/diode/heatsink/connector/terminal losses and temperatures; adequate delivered motor voltage | Brushes/conveyor remain disconnected until reviewed |
| B07 | Wheel-side module capability | Two summed motors per IBT-2; actual board/chip/heatsink/connector continuous/start/stall capacity and fault behavior | Wheel pair power stages |
| B08 | Independent cutoff hardware missing | Selected DC K1 main/coil/two NO auxiliary sets, S0, S2 three isolated NC contacts, S3, coil suppression; actual manufacturer terminal mapping, low-current contact suitability, DC interruption/release and normal manual-reset tests | Independent motor-power/enable cutoff; simple seal-in does not cover held S3/welded contacts |
| B09 | Rail protection/supervisor assemblies unselected | OV1/OV2 output OVP/OCP and isolated fail-open power-good coil contacts, correct supply/fault behavior and threshold tolerance/response; may require several actual parts | Cannot assume an LM2596 protects against output overvoltage or unsafe brownout sequencing |
| B10 | Battery protection and pack data | Chemistry, C rating/condition, maker's cell limits; selected P1 high-side 3S protection/current rating; actual balanced-sense connector order and lead protection; appropriate balance charger | Battery, balance harness and protected bus connection |
| B11 | Fuse/wire/connector selections | F0/FL/FR/FA/F1/F2/FK/FM1–7 ratings and curves, source fault current/DC interrupt capacity, smallest lead/connector limits, lengths/ambient/voltage drop, coordinated motor/driver fault survival | No numeric fuse or AWG/mm2 selection approved |
| B12 | Noise, regeneration and heat | Actual recirculation paths; local reservoir capacitance/ESR/voltage, Z_L/Z_R/Z_A and Z_COIL clamp energy/release behavior, wiring EMI and mounting/isolation measurements | No arbitrary capacitor/TVS or 'driver current limit makes it safe' assumption |
| B13 | Buck/USB/power sequencing | Independent 5.00 V adjustment/load/ripple/fault tests, actual DevKit USB isolation/backfeed, safe power-up/down of connected inputs, proper common-negative paths | Electronics power and mixed USB/external serial access |
| B14 | Commissioning evidence | Unpowered continuity plus staged logic, independent cutoff, individual/pair/cleaning-load and supervised navigation measurements | Physical work cannot be declared complete from software tests |

## Required additions versus alternatives

`electrical/bom.csv` marks every added item: all resistors, proposed bypass/reservoir/clamp parts, U1, fused current-rated distribution, master/stop/manual-arm/contactor hardware, P1 and OV1/OV2. They are **not present in the confirmed inventory**. A block such as OV1 is a functional requirement; no vendor module or footprint has been fabricated to make the drawing look finished. Its actual implementation must be selected and remapped before wiring.

U1 provides a concrete 5V-buffer interface if the actual boards accept 5V logic, and the six ECHO resistors provide a concrete divider if actual signal margins pass. Verified existing board-level conditioning/protection could justify removing or replacing a proposed addition, but only through an explicit design revision and checks. Do not add another motor driver by default; the one-L298N architecture stays provisional until B06 resolves. If its ratings are inadequate, report it unsuitable instead of adjusting software to hide an electrical overload.

## Practical completion essentials

F01–F03 drawing/export defects are corrected in the [audit follow-up](FINAL_ELECTRICAL_AUDIT.md#11-correction-follow-up--f01f03-closed). **Every physical blocker B01–B14 remains open.** The following is a completion list, not approved purchasing ratings or permission to energize the rover.

| Essential item under the present E1 proposal | Still required |
|---|---|
| Sensor and control interfaces | R23–R28 ECHO dividers or a qualified alternative; U1 SN74AHCT244N, R1–R22/R29 default-low networks and local bypassing. Resolve safe behavior with one rail unpowered; ordinary divider calculations alone do not close that requirement. Real ECHO stays disconnected. |
| Protected supplies and battery | Selected implementations of OV1/OV2 OVP/OCP/supervision and compatible high-side 3S P1 protection, protected cell-sense wiring and a pack-compatible balance charger. These are functional requirements pending actual part selection. |
| Independent cutoff | Rated S0, K1 main contact/coil/two auxiliary sets, latching S2 with three isolated NC contact functions, momentary S3 and qualified coil suppression. |
| Distribution and fault protection | Fourteen proposed fuses/holders with coordinated ratings/curves, appropriately rated wire/connectors/terminals and strain relief. No motor-current breadboard or jumper-wire path. |
| Recirculation, noise and heat control | Verify actual board flyback/bypass components; select the required local reservoirs/clamps, cooling and insulated mounting from measured load/transient behavior. Avoid duplicating components already verified on a board. |
| Commissioning equipment access | Suitable multimeter, current-limited bench source, controlled loads, oscilloscope and appropriate current/temperature measurement methods. Availability is not assumed; initial load qualification is not performed from the LiPo. |

**Essential specifications:** identify actual DevKit/driver/buck/sensor variants and terminal maps; obtain all seven motor voltages/tolerances and running/start/stall demand; establish summed wheel-side demand, both-brush plus conveyor thermal/braking limits, pack chemistry/C rating/cell limits and protection/contact/fuse/wire ratings. Conveyor voltage and shared L298 suitability remain unknown.

**Essential measurements:** unpowered continuity/polarity and internal ground bonds; both buck outputs under load and during faults; raw/divided ECHO and reset/brownout/partial-power GPIO behavior; individual and summed motor start/load/overload/braking currents and temperatures; battery/rail sag, protection clearing, contactor release, residual bus voltage, physical directions, sensing/crosstalk and stopping distance. Use the existing staged assembly guide; no physical gate has passed.

**Optional improvements:** encoders/speed control, current and battery telemetry, improved localization, remote interface and ESP32-CAM. Telemetry is optional; adequate overload and cell protection are essential. Another motor driver is not an automatic requirement: first measure whether the existing stages meet the actual load and fault envelope.

## Release record

For each blocker record exact evidence, measured values/instruments, actual manufacturer part numbers, reviewer and date. No row is closed in this package. A low-voltage bench test can release a specific signal interface; it does not release battery or motor branches. Generic safety ports and guessed ratings are not an assembly release.
