# Wiring documentation index — E2 physical design

Current instructions: [READY_TO_WIRE.md](READY_TO_WIRE.md); [review](ENGINEERING_REVIEW_E2.md), [purchase list](FINAL_PURCHASE_LIST.md), [GO/NO-GO](FINAL_GO_NO_GO.md).

The authoritative physical proposal is [FINAL_WIRING.md](FINAL_WIRING.md), with [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md), [ELECTRICAL_AUDIT.md](ELECTRICAL_AUDIT.md) and [ELECTRICAL_BLOCKERS.md](ELECTRICAL_BLOCKERS.md). The earlier direct/provisional interface plan is archived under `archive/WIRING_revision3.md`; it is **superseded** by the buffered/protected E2 design.

[Combined PDF package](diagrams/electrical_package.pdf) / [SVG and individual PDF index](diagrams/INDEX.md). Canonical electrical data: `electrical/design.json`; generated connections, terminals and component BOM are in the same directory.

All 16 firmware GPIOs remain unchanged. One L298N channel A drives the two brushes together; channel B drives the conveyor. The physical proposal adds required 5V buffering/pull-downs, three ECHO dividers plus MCU-powered U2 isolation, qualified supply protection, and independent stop/manual power-arm hardware; these additions are not presently confirmed in inventory. The simulator remains resistor-free and is not the physical circuit.

**Physical release remains HOLD. Real ECHO connections stay disconnected. No current, fuse, wire, exact module, voltage-protection or physical-assembly qualification is inferred from simulation.** Generic safety assembly ports are contracts to map to selected parts, not invented vendor pinouts or footprints. No physical upload or power/motor activation was performed.
