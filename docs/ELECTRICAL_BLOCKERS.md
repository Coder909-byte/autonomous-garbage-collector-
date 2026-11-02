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

## Release record

For each blocker record exact evidence, measured values/instruments, actual manufacturer part numbers, reviewer and date. No row is closed in this package. A low-voltage bench test can release a specific signal interface; it does not release battery or motor branches. Generic safety ports and guessed ratings are not an assembly release.
