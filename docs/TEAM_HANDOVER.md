# Team assembly handover - E2 baseline d6cd479

[Open the team PDF](../artifacts/TEAM_ASSEMBLY_HANDOVER.pdf). This is a focused assembly handover, not a new master review. E2 sources, GPIOs and firmware are unchanged. Physical power-up HOLD remains; checkpoint A and identified unpowered portions of B/C/D can proceed.

## Start here

Keep battery main/balance, USB and every source disconnected; motor ends isolated. Start checkpoint A: mark FRONT, label every module/motor, dry-fit mounts and guards, measure routing with string, and send top/underside/ruler photographs. Keep battery detached. Do not terminate unknown-rated power branches.

No hardware photographs were supplied. Exact images needed: [photo request](hardware_photos/README.md). Actual terminal matches remain unverified.

## Purchase now

| Item | Qty | References |
|---|---:|---|
| SN74AHCT244N | 1 | U1 |
| SN74LVC3G34DCU | 1 | U2 |
| 2.2k 1%, >=1/8 W resistor | 4 | R23, R25, R27, R5 |
| 3.3k 1%, >=1/8 W resistor | 3 | R24, R26, R28 |
| 10k 1%, >=1/8 W resistor | 22 | R1, R2, R3, R4, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R29 |
| 100nF, >=10V ceramic capacitor | 5 | C_U1, C_F, C_L, C_R, C_U2 |
| 100k 1%, >=1/8 W resistor | 3 | R30, R31, R32 |

Obtain a carrier matching U2 DCU VSSOP8 only after checking its mechanical/pad/header map. Power/current-dependent hardware is conditional; use [E2 purchase specification](FINAL_PURCHASE_LIST.md).

## Connection records

The PDF uses all 201 E2 records: 197 external segments, plus W042/W044/W046/W048 as existing internal-bond inspections, never added wires. The generated [connection register](team_handover/TEAM_CONNECTION_REGISTER.csv) retains canonical source, destination, color, net/status and protection, adding intermediate-component explanation, rating criteria and stage-aware verification.

Use blank evidence templates: [wire readings](team_handover/TEAM_ASSEMBLY_RECORD.csv), [terminal mapping](team_handover/TEAM_TERMINAL_MAP.csv), [measurements](team_handover/TEAM_MEASUREMENT_RECORD.csv), [checkpoint record](team_handover/TEAM_CHECKPOINT_RECORD.csv). Preserve originals; copy templates to dated team evidence batches rather than overwriting generated masters.

## What stays disconnected

Battery main and balance, all actual motor loads/high-current branches, unselected P1/OV1/OV2/K1/contact ports, external buck/MCU power and real ECHO-to-MCU plugs. Do not bypass missing protection, hard-enable drivers, parallel buck positives, connect a motor output to ground, or add four internal-bond jumpers. Identified detached signal/protection assemblies may be prepared unpowered; full harness termination waits for its actual pin/rating evidence.

## Checkpoints and remote evidence

Order: A -> applicable B -> C plus D -> E -> F -> G -> I motor-free preflight -> H -> I loaded confirmation -> J. All energized F-J stages are NOT RELEASED. Each checkpoint in the PDF gives instructions, photographs, measurements, PASS and STOP criteria.

### A - Unpowered mounting and labeling

AVAILABLE: dry-fit and label, no electrical power

Send: A batch: P00/P07 images, reference inventory, layout with FRONT arrow, dimension/route-length sheet, list of missing items.

### B - Protected signal-interface assembly

UNPOWERED ONLY: after fixed parts and carrier map verified

Send: B batch: P09 photos, carrier pin-map worksheet, passive-value/continuity readings, solder inspection and any deviation marked unresolved.

### C - Unpowered wiring and continuity checks

AVAILABLE FOR IDENTIFIED SEGMENTS; unresolved routes stay open

Send: C batch: TEAM_ASSEMBLY_RECORD.csv with completed/pending rows, terminal maps, harness photos and explicit unresolved wire-ID list.

### D - Physical component identification and measurements

LABELS/DATASHEETS AND UNPOWERED METHODS ONLY NOW

Send: D batch: P01-P11 originals, manufacturer PDFs, terminal mapping, completed/remaining D01-D06 worksheet and current_budget.csv values with evidence.

### E - Component-dependent electrical completion

HOLD: actual selection and mappings required; completion remains unpowered

Send: E batch: approved BOM/rating calculations/datasheets, as-built terminal and connection records, protection/contact photos, explicit outstanding stage gates.

### F - USB-only firmware installation

NOT RELEASED: future isolated DevKit procedure

Send: F batch: detached-board photo, commit/build/upload logs, serial startup log and operator/date; preserve older installed firmware status until this is actually done.

### G - Regulated power testing

NOT RELEASED: staged current-limited bench tests only after evidence

Send: G batch: wiring/current-limit photos, measured table, original scope captures, ripple/load/thermal/protection records and accepted substep list.

### H - Individual motor testing

NOT RELEASED: approved low-energy tests; cutoff first for driver tests

Send: H batch: per-motor/pair/cleaning tables, current/time/thermal originals, polarity updates, guarded direction videos and any required driver-revision proposal.

### I - Emergency-stop testing

NOT RELEASED: motor-free preflight before H; loaded confirmation afterward

Send: I batch: contact maps, dummy-load preflight record before H, original timing/voltage traces, reset-sequence video and later loaded confirmation; no current result is prefilled PASS.

### J - Complete autonomous operation

NOT RELEASED: all earlier physical gates and supervised trial plan required

Send: J batch: final as-built photos/records, installed commit/hash, trial logs/video, quantitative speed/current/heat/stop data and signed configuration-specific verdict.

## Exact missing measurements

- **D01 / Actual modules and terminal maps** (D now: labels/data): Board manufacturer/revision, every used printed terminal and orientation; U1/U2 package-to-adapter map; correct links/regulator mode; maker schematics for DevKit, BTS, L298 and bucks. Acceptance: One-to-one E2 functional-port to actual printed terminal map, readable photos/datasheets. Unreadable/unmarked terminal remains unconnected.
- **D02 / Battery specification and condition** (D now: pack data): Chemistry, cell count, charge/discharge limits, continuous/peak C and duration, condition, main/balance connector identification and manufacturer sense order; fault envelope from documented data, never a battery short test. Acceptance: P1, charger, contact/fuse voltage/current and sense wiring selected against actual pack limits, not nominal 11.1V alone.
- **D03 / All seven motors** (D data first; H later approved isolated tests): For each M1-M7: part/rated voltage and permitted range, load/run current, start peak and duration, stall current and permitted duration, insulation/pigtail limits; conveyor voltage specifically. Use manufacturer data or separately approved low-energy characterization, never hand-held stalling. Acceptance: Voltage and RMS/run/start/stall envelopes fit motor, driver, connector and coordinated cutoff limits; missing current profile prevents final power selection.
- **D04 / Summed driver and thermal budgets** (D data / E selection; H later confirmation): M1+M2, M3+M4 and M5+M6 totals, simultaneous M7 demand; documented board derating, delivered motor voltage, diode capacity, ambient/case/heatsink temperatures and thermal path; start/stall clearing limits. Acceptance: All continuous/pulse/thermal/voltage limits met simultaneously with stated margin; L298 failing any limit triggers a reviewed replacement revision.
- **D05 / Harness, fuse and contact ratings** (A/C/D unpowered; E selection): Each branch/pigtail material/size/connector rating, one-way route length, ambient/bundling, allowed voltage drop, start/fault I-squared-t and source DC interruption envelope; contactor main/inrush/break and coil voltage/current range across loaded pack. Acceptance: Fuse clearing precedes smallest protected lead/motor/driver allowable overload; voltage drop/temperature acceptable; contacts and holders documented for DC service. No guessed AWG or fuse amperage.
- **D06 / Continuity and isolation** (C unpowered only): Record test-lead resistance; each external segment end-to-end ohms, neighboring-net isolation and polarity with intended sensitive electronics detached; inspect four existing bonds separately. Identify any semiconductor path in context. Acceptance: Expected path agrees with conductor/lead budget, no unintended cross-net link; lead-resistance-corrected values reviewed. Never megger connected electronics or meter resistance across a live battery.
- **D07 / Regulators and rail protectors** (G only after release): Each buck output no-load/peak load, startup/turn-off peak, ripple, temperature and OVP/OCP/UV/power-good response over approved input range; raw and protected outputs separately, dummy loads first. Acceptance: 5.00V target; protected healthy envelope 4.75-5.25V or tighter actual part limits, rated peak load/heat, fail-open coil-permissive response verified. Scope fast peaks; do not intentionally expose MCU to a buck fault.
- **D08 / ECHO, enable, reset and partial power** (G only after release): Raw/divided/U2-output HIGH/LOW, overshoot, rise/fall rate under actual harness, MCU/logic rail order and backfeed, GPIO14 and all six enables through boot/reset/brownout, summed receiver loads. Acceptance: U2 input HIGH >=2.0V, LOW <=0.8V, 0-5.5V and <=10ns/V edges at specified VCC; GPIO levels within ESP32 limits; no unsafe EN pulse/backfeed or raw 5V GPIO path. Use isolated test fixtures before MCU attachment.
- **D09 / Cutoff, restart and stored energy** (I only after release; repeat after H): K1 dropout/coil range, stop-contact continuity, enable fall, bus residual voltage/discharge, normal manual reset sequence, held-reset/weld limitations, suppression and worst braking/regeneration peak/energy. Acceptance: Physical S2 removes all motor power independently of firmware, opens enable and drives GPIO27 LOW; release alone with S3 released does not restart. Clamp/reservoir and discharge/stopping limits supported by reviewed data/traces.
- **D10 / Direction and actual vehicle operation** (H/I/J only after release): Each motor direction and permitted low-energy current, paired run/starting profiles and heat, brush inward sweep/conveyor transport, sensor/crosstalk ranges, actual speed/stopping distance at worst intended floor/load and supervision envelope. Acceptance: Physical directions correct, currents/heat inside approved limits; no auto restart, safe distance margin and guards; controller/simulation results alone never satisfy these measurements.

## Rebuild and validate

```sh
.venv/bin/python scripts/generate_team_handover.py
.venv/bin/python scripts/check_team_handover.py
```

The PDF reuses E2 vector PDF pages without changing them, includes a proposed top-down placement and all 13 requested sections, and carries bookmarks/page numbers. Generator inputs and included diagrams are fingerprinted in `docs/team_handover/manifest.json`. No virtual check establishes physical compatibility.
