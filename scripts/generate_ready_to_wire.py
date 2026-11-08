#!/usr/bin/env python3
"""Generate sectional assembly instructions directly from the canonical wire table."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    'A. ESP32, logic buffers and bias components', 'B. Ultrasonic sensors',
    'C. BTS7960 drivers', 'D. Cleaning driver', 'E. Wheel motors',
    'F. Brushes', 'G. Conveyor', 'H. Buck converters and rail protection',
    'I. Battery distribution', 'J. Emergency-stop system',
]

def section(row):
    refs={row[k].split('.')[0] for k in ('source','destination')}
    if refs & {'M1','M2','M3','M4','FM1','FM2','FM3','FM4'}: return 4
    if refs & {'M5','M6','FM5','FM6'}: return 5
    if refs & {'M7','FM7'}: return 6
    if any(r.startswith('US_') for r in refs) or refs & {'R23','R24','R25','R26','R27','R28','C_F','C_L','C_R'}: return 1
    dest=row['destination'].split('.')[0]
    if dest in {'DRV_L','DRV_R'} or dest in {'C_BL','C_BR','Z_L','Z_R'}: return 2
    if dest in {'DRV_A','C_BA','Z_A'}: return 3
    if refs & {'K1','S2','S3','FK','Z_COIL'}: return 9
    if dest in {'BUCK1','BUCK2','OV1','OV2','F1','F2'}: return 7
    if dest in {'BT1','F0','S0','P1','TB_POS','TB_GND','FL','FR','FA'}: return 8
    return 0

def generate(rows):
    s='''# Ready-to-wire reference — E2, 8 November 2026

**ASSEMBLY RELEASE HOLD.** This is the complete connection instruction set for the proposed design, not permission to connect battery power. P1, OV1/OV2, K1 and all current-dependent selections still require actual hardware and terminal mapping. See [final decisions](FINAL_GO_NO_GO.md), [review](ENGINEERING_REVIEW_E2.md) and [purchase list](FINAL_PURCHASE_LIST.md).

Keep the battery main and balance connectors, USB, all supplies and motor loads disconnected during continuity work. No powered hardware work or firmware upload was performed for this package. A switch does not isolate battery cell-tap leads. Do not fit links across missing protection blocks.

Each numbered step is one canonical connection. Source and destination include component reference and pin/terminal; use the component legend in [FINAL_WIRING.md](FINAL_WIRING.md). `INTERNAL_VERIFY` means inspect an existing internal module connection, **do not install an extra wire**. All other rows are conductors; a common net may require a rated terminal block/splice with enough positions. Never stack unqualified lugs or route high current through a signal header. Generic names such as K1.MAIN_COM, P1.CELL1, OV1.PG_NO and ESP1.5V_VIN are functional ports, not verified manufacturer terminal numbers. All numbered U1/U2 pins refer to the identified IC package; adapter header numbering requires its own mapping.

For each row: (1) resolve its HOLD using actual part data, (2) confirm terminal markings and polarity, (3) fit the identified protected conductor while unpowered, (4) continuity-check it and check isolation from neighboring nets, (5) record wire ID and inspection. The stated voltage is a later test expectation, not an instruction to energize. Red is supply, black return, blue control, green sensor, orange bridge output; motor outputs are reversible, not fixed battery polarity.

ESP32: preserve all 16 GPIOs. U1 is AHCT, never HC; OE pins 1/19 to GND, VCC20 to protected logic 5V, GND10 to logic return. Fit R5=2.2k at GPIO14/U1.11 and all local pulls. U2 is SN74LVC3G34DCU, powered from ESP32 3V3 only. Its channel map is 1->7 (front), 3->5 (left), 6->2 (right), VCC8, GND4. Fit C_U2 and output bias R30–32; never bypass U2 or a divider. Direct virtual Wokwi connections do not represent physical conditioning.

Drivers: remove both BTS hard-HIGH enable links if fitted; verify actual module input loads and internal B-/GND bonds. Insulate R_IS/L_IS separately. L298 ENA/ENB links must be removed; disable the onboard regulator according to its verified schematic before applying external 5V logic. Check eight recirculation paths and local Vs/Vss bypassing. Do not confuse its regulator jumper with ENA/ENB. No driver is load-approved.

Motors: M1/M2 left parallel, M3/M4 right parallel, M5/M6 parallel across cleaning OUT1/OUT2, M7 across OUT3/OUT4. Each A lead passes through FM1–7; returns go only to the paired bridge output, never GND. The fuse voltages must cover either bridge polarity and the documented fault envelope. Actual fuse currents remain TBD. Later, under an approved current-limited isolated test source with guards and lifted wheels, pulse one motor briefly at a permitted voltage. Mark leads A/B by observed mechanical travel, not insulation color. Reverse the necessary motor leads while isolated so all wheels propel forward, brushes sweep inward and conveyor carries waste into the bin. Record deviations to the wire table before paired tests. Never stall a gearbox by hand.

Power: both buck inputs come from the protected battery distribution **before K1**, on independent F1/F2 branches. Adjust each to 5.00V under a qualified current-limited bench procedure with all electronics removed; qualify load/ripple/OVP before connecting loads. Never parallel their positive outputs or feed 5V to 3V3. Motor bus K1 feeds only FL/FR/FA. Use a heavy ground star; inspect internal bonds instead of creating thin parallel motor returns. USB-only programming requires detached external harnesses until the board's USB/external supply path is qualified. No USB backfeed solution is assumed.

E-stop: S2 opens three isolated NC paths (coil, enable, sense). K1 has a main NO plus separate seal-in and sense NO contacts. Two fail-open isolated rail-healthy contacts precede the coil; their implementations remain unselected. S3 is a momentary hardware power-arm, distinct from serial ARM. GPIO27 is HIGH healthy from ESP32 3V3 through S2 sense NC and K1 sense NO, with 10k external/internal pull-down. An open K1 at boot intentionally latches ESTOP. Later guarded commissioning requires outputs disarmed and EN verified LOW, deliberate S3, healthy GPIO27, then RESET and ARM. Releasing S2 alone with S3 released must not restore motor power. A stuck S3 or welded contact is outside this single-channel circuit's fault coverage. Serial ESTOP disables EN/PWM but does not open K1 or isolate power.

The sections below are wiring groups, not an authorization to energize them sequentially. Full protection/verification details are retained verbatim from the connection model.
'''
    def esc(x): return str(x).replace('|','/').replace('\n',' ')
    step=0
    for i,title in enumerate(SECTIONS):
        s+='\n## '+title+'\n\n'
        s+='| Step / wire | Source component.pin | Destination component.pin | Purpose / net | Expected voltage | Protection / route / dependency | Verification |\n|---|---|---|---|---|---|---|\n'
        for r in rows:
            if section(r)!=i: continue
            step+=1
            cells=[f"{step} / {r['wire_id']}",r['source'],r['destination'],r['net']+'; '+r['signal_type'],r['voltage'],r['protection']+'; '+r['connection_kind']+'; '+r['status']+'; '+r['conductor_class'],r['verification']]
            s+='| '+' | '.join(map(esc,cells))+' |\n'
    assert step==len(rows)
    return s

if __name__=='__main__':
    with (ROOT/'electrical/connections.csv').open() as f: rows=list(csv.DictReader(f))
    (ROOT/'docs/READY_TO_WIRE.md').write_text(generate(rows))
    print(f'Generated {len(rows)} unique assembly steps in sections A–J')
