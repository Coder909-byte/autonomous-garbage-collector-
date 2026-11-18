# Commissioning status — retained user reports

Source: the owner's supplied results in this project conversation, retained in
[TEAM_MEASUREMENT_RECORD.csv](TEAM_MEASUREMENT_RECORD.csv). Twelve individual
checks, D06.U01–U12, are **COMPLETE — USER-REPORTED (observation only)**. This
records completed work; it is not independent review or full commissioning PASS.
Test timestamps, instrument identity, trace files and reviewer/date were not
supplied and have not been invented. Power/isolation and connected-load conditions
were not supplied for the resistance/continuity readings.

## Mapping to the six firmware requirements

| Requirement | Evidence already retained | Specific outstanding evidence |
|---|---|---|
| `driverInterface` | SN74AHCT244 installation reported; ESP32-to-both-driver PWM/enable continuity; both VCC and ground paths confirmed (D01, D06.U01–U03). **Partial.** | Exact installed interface/terminal mapping and measured HIGH/LOW levels at loaded driver inputs, including shared enable fanout. |
| `motorPowerProtection` | Fuse protection installed and motor-current ratings checked, as reported (D03, D05). **Partial.** | Actual fuse/holder, wire/connector and pack/protection ratings; retained numerical motor-current limits/source and protection coordination. |
| `independentDisconnect` | DC disconnect installed; both switched motor-positive paths continuous ON and open OFF (D06.U11, D09). **Partial.** | Disconnect DC rating and motor-free measurement of downstream supply removal/residual voltage with ESP32/software independent of the switch. |
| `failOff` | Static PWM/enable continuity retained. **Dynamic behavior outstanding.** | Scope captures showing driver enables/PWM remain inactive through startup/reset, controlled brownout and control-power loss/recovery; no unexpected restart. |
| `supplyAndGround` | Both driver grounds and ESP32 GND continuous to buck OUT−; buck IN−/OUT− continuity; supplied buck resistance observations (D06.U02, U06–U10). **Partial.** | Loaded/unloaded regulated voltage, startup/ripple envelope and relevant power sequencing; actual DevKit USB/external-power path and reverse-current/backpower measurements. |
| `motorCurrentAndThermal` | User reports motor-current ratings checked; both pairs connected to respective M+/M−; output resistance observations retained (D03, D06.U04/U12). **Partial.** | Numerical ratings and source; actual run/start current and duration, supported stall limits, paired-driver totals, driver/connector temperatures and test conditions. Include cleaning loads if they are in the commissioned configuration. |

The buck input overrange on **20 kΩ**, output approximately **1.21 kΩ**, and
motor outputs approximately **20 Ω left / 10 Ω right on the 20 kΩ range** are
preserved exactly as reported. The buck output resistance range was not supplied.
The motor reading units/display interpretation remain unconfirmed without the
original display/notes. No-beep/overrange results establish neither infinite
resistance nor powered isolation. Motor resistance is not current/thermal evidence.

## Next actionable verification

**Retain the actual rating values/source from the checks already completed, then
perform the missing motor-free rail and startup/reset fail-off measurements.**
Do not repeat the documented continuity checks.

1. Keep wheel-motor power isolated. Using the installed hardware's qualified,
   current-limited bench arrangement, record buck unloaded/loaded output voltage
   before proceeding with the affected logic loads. Use actual component limits.
2. Capture GPIO14, GPIO16–19 and both BTS7960 R_EN/L_EN receivers through power-on
   and ESP32 EN/reset. Record the relevant logic rails alongside the outputs.
   Extend to controlled rail loss/brownout/recovery only with a suitable bench
   fixture. Retain waveforms showing no unintended driver enable or PWM, with
   instrument settings, endpoints, conditions and reviewer/date. A continuity
   meter cannot supply this evidence. Do not bypass the firmware interlock.
3. Resolve USB backfeed separately from the actual DevKit power-path documentation
   and an instrumented, current-limited fixture covering USB-only, external-only
   and relevant sequencing cases. Record VBUS/rail voltage and reverse current;
   do not use the Dell as an unqualified backfeed test load.

The remaining current/thermal and energized disconnect measurements stay open
until their real results are retained. None of these partial records closes the
firmware release record; `rover_commissioning.h`, firmware, GPIO assignments,
ESP32-CAM, upload ZIPs and working dashboard are unchanged.
