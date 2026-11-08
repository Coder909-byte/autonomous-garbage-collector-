# Staged physical assembly and commissioning guide — E2

Current E2 connection authority is [READY_TO_WIRE.md](READY_TO_WIRE.md) with [ENGINEERING_REVIEW_E2.md](ENGINEERING_REVIEW_E2.md); direct divider-to-GPIO E1 instructions are superseded.

**This is a future procedure, not an executed test or an instruction for the agent to power hardware.** Firmware was not uploaded and no battery/motor was energized during package creation. A passed software test does not release an electrical hold. Follow [FINAL_WIRING.md](FINAL_WIRING.md), the numbered wire rows in `electrical/connections.csv`, and [ELECTRICAL_BLOCKERS.md](ELECTRICAL_BLOCKERS.md).

Do not start affected wiring while protection parts, actual terminal mapping or ratings are unresolved. Required tools include a suitable multimeter, continuity tester, appropriately current-limited bench sources/dummy loads, and an oscilloscope for pulse/ripple/reset checks; availability is not assumed. Have qualified supervision for energy-bearing work. Never use a meter's current range directly across a battery or supply. Configure current measurement with the supply disconnected first. Stop on an unexpected reading; do not bypass an interlock to get a test to run.

## 1. Unpowered wiring inspection — steps 1–15

1. Unplug BT1 main connector **and balance connector**, USB, all bench sources and all seven motor leads. Remove motor branch/lead fuses; leave K1 open and S2 latched OFF. Confirm the motor bus and capacitors are discharged with the meter before touching conductors.
2. Identify the exact DevKit variant, BTS boards, L298 module, buck boards, motors, battery and all added protection parts. Record manufacturer part numbers/photographs locally and map actual terminal order to the functional labels. Do not guess physical header position from GPIO number.
3. Resolve every relevant HOLD in the blocker sheet before installing its branch. No resistors/level shifters are presently stocked. Do not install a raw ECHO wire or substitute a high enable jumper for missing parts.
4. Inventory the full BOM. Ensure P1, OV1/OV2, K1/contacts, S2/S3, fuse holders, resistors and suppression are actual selected assemblies with reviewed voltage/current/terminal information. Generic ports in the drawings are not vendor pinouts.
5. Label both ends of every planned wire by its `Wxxx` ID, net, source terminal and destination. Choose actual wire gauges/lengths, connectors, crimp tools and fuse curves only after completing the current worksheet. No solderless breadboard or Dupont lead in a motor-power path.
6. Mount insulated distribution, drivers and bucks with strain relief and protected terminals. Check module heatsink/tab/mounting-hole isolation; do not assume heatsinks or motor cans are GND. Keep battery restrained and protected from puncture. Do not use chassis as motor return.
7. **Connect the return harness first, still unpowered:** BT1 negative lead endpoint to TB_GND; dedicated DRV_L B-, DRV_R B- and DRV_A GND returns to TB_GND. The battery itself remains unplugged. Inspect/check the required existing BTS GND/B- bonds; do not create a second thin parallel motor return.
8. Next connect each BUCK IN- to TB_GND. Verify actual non-isolated IN-/OUT- continuity. Route ESP1 GND to BUCK1 OUT- and U1/sensor logic returns to BUCK2 OUT-. Check every black-wire endpoint and R/cap ground in the connection table. Do not add unnecessary parallel ground jumpers.
9. Fit passive conditioning on an insulated board: U1 per the exact 20-pin diagram; R1–R8, with R5 specifically 2.2k at GPIO14; six local EN pull-downs R13–R18; PWM pulls R19–R22; auxiliary-input pulls R9–R12; R29 at GPIO27; proposed bypass capacitors. Confirm resistor values with power off. All these parts must first be obtained.
10. Fit U2 SN74LVC3G34DCU per READY_TO_WIRE.md: VCC8 to ESP32 3V3, GND4 to ESP32 GND; channels 1->7 / 3->5 / 6->2; C_U2 local 100nF and 100k output pulls R30–32. Prepare R23/24, R25/26 and R27/28 ECHO dividers. Verify upper=2.2k and lower=3.3k, 1%; independently trace the node and GND. **Leave both the real ECHO-to-divider and U2-to-ESP plugs disconnected** until stage 4 passes, including U2 input edge rate <=10ns/V, output levels and off-rail leakage.
11. With actual-board instructions established, remove L298 ENA/ENB hard-HIGH links. Identify the separate onboard regulator link; disable that regulator only in its documented external-5V mode. Confirm neither a GPIO nor a buck will be driven against a jumper/regulator output. Verify flyback diodes; do not assume a clone contains suitable ones.
12. Connect the blue control harness to the documented terminals: GPIO16/17/18/19/14 and three TRIGs via U1; GPIO21/22 to L298 IN1/2; GPIO23/25 to IN3/4. U1 output9 goes through the separate S2 enable NC contact to all six driver enable terminals. Check each terminal independently, not just one point on the enable bus.
13. Wire isolated stop feedback as 3V3 -> S2 sense NC -> K1 **sense** NO -> GPIO27. Do not use K1's coil seal-in contact for GPIO feedback. Verify complete isolation from coil/5V circuits and correct LOW bias on an open loop. Keep R_IS/L_IS separately insulated and camera disconnected.
14. Prepare positive power routing with the battery unplugged: pack harness -> F0 -> S0 -> P1 -> TB_POS, separate input fuses for bucks, K1 main NO -> FL/FR/FA, and individual motor-lead fuses. **Do not wire balance contacts or unselected safety blocks by the diagram's functional port name alone.** Manufacturer balance/sense protection and pin order must be established first. Motor lead ends remain isolated; fuses remain removed.
15. Complete a point-to-point resistance/continuity record for every W row. Check adjacent terminals for shorts, all power polarities, no H-bridge output to GND/chassis, no positive buck outputs paralleled, and no unintended 5V-to-GPIO path. Meter continuity alone does not certify semiconductor paths; interpret resistance through module circuitry using its schematic.

## 2. ESP32 USB-only programming — steps 16–21

16. Disconnect the ESP32 external power and complete external GPIO harnesses. Keep battery/balance/bench supplies and motors unplugged. Only the DevKit and approved USB cable may be powered at this stage.
17. Build/check without upload first: `.venv/bin/python scripts/verify.py`. Use the pinned `esp32dev` environment and correct actual board/port.
18. If a later owner-run upload is needed, use PlatformIO's Upload action only after confirming step 16. No upload is part of the current automated verification. Do not use any automatic motor-test-on-upload procedure.
19. Open Serial Monitor at 115200 baud, Newline. Expect READY/DISARMED and low requested outputs. Unwired GPIO27 reads unsafe through its internal pull-down; an ESTOP latch is expected. Do not bridge it HIGH to defeat the physical feedback design.
20. Send STOP or ESTOP and verify disarmed/latch reporting. ARM must be rejected while the feedback input is unsafe. This proves commands/logic only, not output voltage at a real driver.
21. Disconnect USB and verify no external rail has unexpectedly become powered. Restore the prepared harness only while unpowered and only after its own stage gates pass.

## 3. Buck converter adjustment and protection — steps 22–31

22. Keep ESP32, sensors, drivers and motor loads disconnected from both bucks' outputs. Keep BT1 main/balance unplugged. Use a suitable isolated, current-limited bench source, not the LiPo, for adjustment.
23. Check BUCK1 IN+/IN- polarity and source voltage against the actual module input rating. Connect source with output disabled, then enable only the low-energy bench setup. Measure across OUT+/OUT-; adjust to **5.00 V** without electronics attached.
24. Disable/disconnect the source. Repeat independently for BUCK2. Never join the two OUT+ rails. Confirm common negative continuity only while unpowered.
25. Load-test each buck using an appropriate dummy load from the measured MCU/logic budget. Record output voltage, input/output current, temperature and startup/shutdown behavior. A chip's 3 A label does not establish the module's continuous current.
26. Scope ripple and overshoot through the intended input range and load steps. A DMM average is insufficient. Qualify the 4.75–5.25 V envelope and any tighter actual-device limit; select local bulk/EMI parts from the measured data.
27. Qualify the selected OV1/OV2 OVP/OCP/supervisor assemblies separately with electronics disconnected. Test their trip/restore voltage, tolerances, delay, peak let-through, fault-current limit, default-open power-good contacts and behavior when unpowered. Use controlled bench inputs within equipment limits, not a deliberately failed buck on the rover.
28. Connect each qualified buck through its OV stage into a dummy load. Verify protected output and both isolated coil-permissive contact functions. No unverified logic rail is allowed to connect to the ESP32/sensors.
29. Qualify P1 and its cell-sense adapter per manufacturer instructions with appropriate isolated cell-simulation/test equipment. Do not deliberately overcharge/overdischarge a LiPo or improvise a balance-pin sequence. Record actual cutoffs, current ratings, safe sense-lead protection and high-side operation.
30. With all sources off, connect protected V5_MCU only to the actual DevKit's approved regulated-5V/VIN input. Connect protected V5_LOGIC only to qualified U1/sensor/driver logic inputs. Recheck L298 regulator isolation and correct GPIO/3V3 exclusion.
31. Decide and verify the supported USB/external-power arrangement. Use one power input, or a reviewed board-specific data/isolation arrangement or suitable 3.3 V UART interface with its VCC disconnected. Do not assume a cable or onboard USB diode prevents backfeeding. Scope rail sequencing and do not drive unpowered modules through GPIOs without specification support.

## 4. Sensor voltage verification — steps 32–39

32. Keep motor supply fuses and all motor leads removed. Keep real ECHO plugs disconnected from ESP32. Power only the already qualified low-voltage logic arrangement; use controlled bench sources initially.
33. Measure each actual sensor VCC at its connector and its GND reference. Identify exact module/output documentation if available. Standard HC-SR04 supply/output behavior cannot establish a special 3.3 V output on an unidentified clone.
34. Confirm U1 trigger input/output mapping by continuity, then scope the proposed 10 us trigger pulse levels and polarity for front/left/right. Never apply 5 V to the ESP32 side of U1.
35. Measure each ECHO high, low and overshoot independently of the ESP32. Use an appropriate high-impedance instrument and safe probe connection; no MCU GPIO is the test instrument.
36. Connect the actual ECHO only to its verified upper resistor, with the divider output still disconnected from the ESP32. Measure the output high/low/pulse shape. Confirm no wrong resistor order and no missing lower resistor.
37. Confirm divided HIGH is above 0.75*actual ESP32 VDD, LOW below its guaranteed limit, and peak below the GPIO limit, including worst supply/tolerances/noise. Nominal 3.0 V is a calculation, not a measurement. If inadequate, keep disconnected and qualify a real translator; do not bypass the divider.
38. Power down. Only after the voltage gate passes connect front divider to GPIO34, left to GPIO35, right to GPIO36/VP. Trace each wire against labels; never swap these with outputs/5V. Power back up logic only and check each DIST field separately.
39. Inject a safe logic-only sensor disconnection, with motors physically unavailable: AUTO must reject missing data or disarm on invalid/stale readings, and restoring data alone must not restart. No acoustic or electrical physical pass is recorded until the owner actually performs these steps.

## 5. Motor-driver signal and cutoff verification — steps 40–50

40. Keep all seven motors disconnected and all motor-power/lead fuses removed. Use qualified logic supplies. For future serial access, use the already reviewed USB/UART isolation arrangement. Do not power motors to test a control signal.
41. Scope GPIO14/U1 input11, output9, after S2 EN NC, and each driver EN during power ramps, reset, USB activity, brownout and unplugging. All receivers must remain disabled without an explicit firmware move. K1 stays open until rails and EN are verified.
42. Check all four buffered wheel PWM lines and four L298 inputs LOW during reset/disarm. Check no forward/reverse pair is driven together and U1 polarity is non-inverting. Measure actual input current/high/low and shared enable fanout; the calculated 3 mA pull load excludes unknown module loading.
43. Qualify K1 coil supply range and selected suppression with motor power/load disconnected. Confirm actual A1/A2, main contacts and **two separate** NO auxiliary functions; never infer terminal numbers from the generic drawings.
44. Wire/test FK -> OV1 healthy -> OV2 healthy -> S2 coil NC -> (S3 NO || K1 seal-in NO) -> coil. Verify S3 released cannot hold a dropped circuit; S2 press/logic-rail fault/power loss must drop K1. Verify proper contactor release time and no unreviewed coil clamp delay.
45. Verify ESP32 3V3 -> S2 sense NC -> K1 separate sense NO -> GPIO27 independently. With K1 open GPIO27 is LOW and firmware latches ESTOP. Pressing S2 must also open the 5V enable contact; test this independently of software.
46. With EN measured LOW and motor fuses removed, deliberately press S3 to arm contactor power. Check feedback HIGH only with K1 closed and S2 released. Send RESET, then ARM; all motor output requests must stay stopped until a movement command. A held/stuck S3 or welded contact is outside the simple circuit's fault coverage and requires the reviewed safety/reset solution if applicable; do not mark those faults covered.
47. Send MANUAL then a single F. Scope left/right forward PWM and the 1.2 s manual timeout. Repeat B, L, R individually with outputs still unloaded. Confirm at least 100 ms EN-low neutral on a new motion, no opposed PWM, correct frequencies/duties and appropriate receiver voltage margins.
48. During logic-only F, test BRUSH ON/OFF and CONVEYOR ON/OFF independently, then CLEAN ON/OFF. Confirm both brushes share channel A and conveyor is B. Verify cleaning outputs off during turns, reverse, stop and neutral time.
49. Serial ESTOP disables EN/PWM but does not itself open K1 or remove bus voltage. Issue ESTOP while requesting motion; confirm actual EN low, GPIO27/feedback behavior, K1 main opening when S2 is physically pressed, and no restart from releasing S2 or restoring rails. Re-arming always requires deliberate hardware power-arm, healthy feedback, RESET/ARM and a new movement command as applicable. Do not power-arm with stale HIGH EN.
50. Record driver outputs, reset/rail-fault waveforms, main-bus residual voltage/decay, contactor release, and all measured input currents. An ISR test in host stubs cannot substitute for these measurements. Do not progress if an unexplained enable glitch, supply backfeed or weak logic level exists.

## 6. Individual motor testing — steps 51–58 (future gated motor power)

51. Stop here until actual motor ratings, current/thermal limits, branch/motor-lead fuse curves, wire/connector ratings, overload response, emergency cutoff and supply protection are reviewed and documented. Battery stays unplugged for initial controlled bench commissioning. No motor trial is authorized by this guide merely existing.
52. With all power off, secure the chassis with wheels raised and mechanisms guarded. Keep brushes/conveyor disconnected. Prepare one motor circuit only, using a suitable current-limited source and selected fuses; verify it can supply the planned trial without exceeding the reviewed limits. Connect A/B leads only to that driver's H-bridge outputs through the assigned fuse.
53. Before energizing, confirm stop access, no contact with moving parts, safe current-meter/shunt configuration and instruments, and a clear test area. Set initial current/energy constraints from the actual motor/driver data, not from invented values.
54. After the qualified logic/power sequence and EN-low check, the supervising operator may deliberately enable that single motor trial and issue a brief manual command. Measure direction, terminal voltage, running/start current and temperature. Verify deadman, S2 and disarm remove drive. Do not automatically activate on startup/upload.
55. Power off, isolate and discharge before changing leads. Reverse one motor's A/B only if its physical mounting makes direction incorrect; relabel its wire record.
56. Repeat separately for M1, M2, M3 and M4. Establish each motor's startup/stall demand from manufacturer data or a separate appropriately limited fixture; **never jam a wheel directly from the LiPo**. Do not rely on average PWM current as a peak driver limit.
57. Check fuse/overload behavior using a safe test plan that does not exceed component/fixture ratings. Branch fuses alone may not act fast enough for a semiconductor or small motor; unresolved fault protection keeps the next stage blocked.
58. Complete the worksheet and reassess worst-case simultaneous demand. If a measured rating invalidates the proposed driver or protection, revise the design before connecting the paired load.

## 7. Complete drivetrain testing — steps 59–64

59. With power isolated, connect M1/M2 in parallel across the left bridge and M3/M4 in parallel across the right bridge, each through its own qualified lead fuse. Do not parallel the driver boards' outputs.
60. Recheck paired rotation on raised wheels with guarded, controlled-power trials. Measure each side's summed startup/load current, bus droop and driver/terminal/wire temperatures. Both side-mates must agree physically.
61. Test manual forward/reverse/left/right and stopping separately. Verify real neutral time and mechanical coasting/stopping; the software 100 ms interval is not proof a rotor is stationary.
62. Check current/protection coordination for simultaneous starts within a controlled reviewed test, and EMI effects on ESP32 resets/sensors. Tune qualified suppression/reservoir/clamp components from measurements, not arbitrary TVS/cap values.
63. Only after bench tests/protection acceptance, review 3S battery/C rating, cell monitoring, fusing, polarity, restraints and connectors for a later deliberate pack-powered supervised trial. Keep charging separate; no rover-connected charging.
64. Record acceptable current/thermal/bus transient/stopping data before floor operation. No safe runtime/endurance assumption follows from a brief unloaded spin.

## 8. Cleaning-system testing — steps 65–71

65. With power off, attach one guarded brush only to OUT1/OUT2 through its fuse. Verify the one-brush current/direction in an appropriately limited trial, then isolate before trying the second brush alone.
66. Review `I_brush1 + I_brush2` for startup/running/jam against the verified derated channel-A limit; include conveyor heat in the same L298 package. If unsupported, leave the shared stage disconnected. A 2 A absolute maximum is not a module rating.
67. Only after acceptance, connect both brushes in parallel on A. Reverse one pair of leads if required for inward sweeping; they cannot be independently commanded. Keep hands/tools away from both brushes.
68. Verify conveyor motor rated voltage/current first. Test M7 alone on OUT3/OUT4 through FM7 under suitable guards/current limits; do not assume it is 12 V.
69. With the reviewed combined load allowed, issue forward motion plus BRUSH ON/OFF and CONVEYOR ON/OFF independently, then CLEAN ON/OFF. Both outputs must disable on turning/reverse/stop and after timeout/ESTOP. Stationary auxiliary running is not a firmware feature.
70. Record loaded terminal voltages, package/diode/heatsink/terminal temperatures, currents and any brownout. L298 voltage loss may prevent adequate motor torque even below a current limit.
71. Qualify a safe jam/overload response with the reviewed fixture/protection; do not deliberately stall the LiPo-powered rover. No physical jam sensing exists in firmware. Failed current/thermal acceptance means the proposed L298 stage is unsuitable.

## 9. Autonomous navigation testing — steps 72–80

72. Only after every electrical and mechanical gate passes, establish a supervised, cordoned test area with accessible independent stop and no bystanders near wheels/rollers. No rear/cliff detection, encoders or localization exists.
73. Validate actual sensor mounting, acoustic crosstalk, range, reflective/absorbent targets and noise with the rover secured. False plausible ranges cannot be caught by timeout alone.
74. Start DISARMED, establish qualified rails/feedback and deliberate hardware power-arm. Check EN low, send RESET if latched, then ARM. All outputs must remain stopped until AUTO or a manual movement command.
75. With a clear area, issue AUTO and observe initial forward motion. Log distances, `nav=`, `ms=` and measured motor behavior. Record thresholds/stopping margins, rather than assuming the simulated distances fit real inertia.
76. Introduce controlled front/side obstacles. Verify SETTLE, 100 ms neutral, targeted 540 ms enabled turn, stopped reassessment and a new reading from every sensor before recovery. Tune only after measured clearance and stopping data.
77. Verify persistent blockage stops after at most three unsuccessful attempts with TURN_LIMIT; no restart from moving an obstacle alone. Verify explicit ARM/AUTO recovery only with fresh valid ranges and safe environment.
78. Test ESTOP/physical S2, missing sensor and controlled power fault response using the safe fixture established earlier. Do not disconnect high-current connectors under load. No automatic restart on stop release, range restoration or power-good restoration is acceptable within the reviewed design behavior.
79. Test cleaning requests during supervised forward travel only after stages 6–8 pass. Observe motor/sensor noise and heat over an appropriate reviewed duty cycle. Do not infer endurance from Wokwi.
80. Record actual wire/part selections, measurements, photos, pass limits, observer and date. Update model/docs and verification status. Only successful physical testing can establish that the assembled rover works; none is claimed by this package.
