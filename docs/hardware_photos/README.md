# Hardware photograph request - E2 team handover

No photographs were supplied when this handover was prepared. This folder was created for team evidence. No actual terminal label, component marking or rating has been visually verified. Add original-resolution images using these names (PNG is also acceptable); do not expose/open the battery or probe its connectors for identification.

## P00 - whole rover

Files: P00_rover_top.jpg; P00_rover_underplate.jpg; P00_plate_with_ruler.jpg

Front arrow, all mounts, separate cable routes, guarded brush/conveyor clearance, electronics plate dimensions; photograph battery detached.

E2 comparison: Physical layout only; no hidden wire or terminal inference.

## P01 - ESP1

Files: P01_ESP1_front.jpg; P01_ESP1_back.jpg; P01_ESP1_headers_usb.jpg

Readable module can/chip/board revision, GPIO and power labels on both headers, EN/reset and USB connector type.

E2 comparison: Match GPIO16/17/18/19/21/22/23/25/14/27/32/34/33/35/13/36, 3V3/GND and board-approved 5V input. USB power path needs schematic, not just photos.

## P02 - DRV_L

Files: P02_DRV_L_front.jpg; P02_DRV_L_back.jpg; P02_DRV_L_terminals.jpg

Chip/buffer markings, control header order and all screw labels, jumpers/links, connectors and heatsink mounting. Do not dismantle powered equipment.

E2 comparison: B+/B-/M+/M-/VCC/GND/RPWM/LPWM/R_EN/L_EN/R_IS/L_IS, orientation and link configuration; no continuous-current inference.

## P03 - DRV_R

Files: P03_DRV_R_front.jpg; P03_DRV_R_back.jpg; P03_DRV_R_terminals.jpg

Same independent views as DRV_L; include this board's own labels and revision.

E2 comparison: Match this module separately; identify internal B-/GND bond by later unpowered method.

## P04 - DRV_A

Files: P04_DRV_A_front.jpg; P04_DRV_A_back.jpg; P04_DRV_A_jumpers_diodes.jpg

Chip/regulator markings, Vs/5V/GND, OUT1-4, IN1-4, ENA/ENB labels, separate regulator jumper and all recirculation diodes.

E2 comparison: Map actual carrier labels to E2 Vs_12V and 5V_LOGIC functional ports; schematic and thermal/load data still required.

## P05 - US_F / US_L / US_R

Files: P05_US_F_front_back.jpg; P05_US_L_front_back.jpg; P05_US_R_front_back.jpg

Each sensor face/rear and readable VCC/TRIG/ECHO/GND labels, version and mounting direction; paired views may share a photo if legible.

E2 comparison: Three individual header maps; visual appearance does not prove ECHO levels.

## P06 - BUCK1 / BUCK2

Files: P06_BUCK1_front_back.jpg; P06_BUCK2_front_back.jpg; P06_buck_terminals.jpg

Each actual IN+/IN-/OUT+/OUT-, chip, inductor, diode, capacitor voltage markings and adjustment screw.

E2 comparison: MCU versus logic designation and polarity; internal negative bond and capability need measurement/data.

## P07 - M1-M7

Files: P07_M1_label_leads.jpg through P07_M7_label_leads.jpg; P07_motor_mounts.jpg

Each distinct label/part number, rated voltage/speed if printed, gearbox, pigtails/connectors and mechanical direction arrow. Conveyor is a priority.

E2 comparison: Assign motor identities and lead labels A/B provisionally. No operating/start/stall current or direction inferred from color/RPM.

## P08 - BT1

Files: P08_BT1_label.jpg; P08_BT1_connectors.jpg

Intact exterior chemistry/cell/capacity/C-rating/charge information and manufacturer; unplugged main/balance housings without exposing or probing contacts.

E2 comparison: Confirm actual pack specification. Balance pin order must follow manufacturer data; do not unwrap or open battery.

## P09 - U1 / U2 and interface board

Files: P09_U1_mark_pin1.jpg; P09_U2_carrier_both_sides.jpg; P09_interface_top.jpg; P09_interface_underside.jpg

IC order code and pin1, actual carrier model/header markings, resistor reference/value labels, divider nodes, bypass placement and solder joints.

E2 comparison: Verify AHCT244N and LVC3G34DCU, IC-to-carrier mapping and MCU3V3 supply for U2; attach header continuity map.

## P10 - P1 / OV1 / OV2 / K1 / S0 / S2 / S3

Files: P10_<reference>_label_terminals.jpg for each actual selected assembly

Manufacturer/part/revision, complete terminal legends, coil/contact blocks and markings; attach maker datasheet and a function-to-terminal mapping.

E2 comparison: These assemblies are unselected E2 functional ports; photographs alone do not close ratings, thresholds, isolated contact or reset behavior.

## P11 - F0 / F1 / F2 / FK / FL / FR / FA / FM1-7 / TB_POS / TB_GND / clamps / capacitors / harness

Files: P11_protection_parts_labels.jpg; P11_distribution_terminals.jpg; P11_harness_markings.jpg

Actual fuse/holder series and rating/curve references, wire/connector markings, capacitor/clamp codes and polarity, mounting and conductor-length schedule.

E2 comparison: Match approved selections only after current/thermal/fault criteria exist; unmarked parts remain unidentified.

## P12 - checkpoint evidence

Files: P12_<checkpoint>_<view_or_wire_ID>.jpg

Unpowered overview, each terminal strip close-up, both ends of labeled harnesses; probe endpoints and instrument display for ambiguous/changed routes. Provide a reading row for every connection, not 201 repetitive photos.

E2 comparison: Tie every measurement and photo to wire IDs/checkpoint; preserve originals and explain any deviation.

Fill `docs/team_handover/TEAM_TERMINAL_MAP.csv` from visible labels and actual manufacturer documentation. Missing or unreadable values stay PENDING. Photographs require review; filenames alone are not evidence of compatibility.
