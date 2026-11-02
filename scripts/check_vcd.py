#!/usr/bin/env python3
"""Check actual Wokwi analyzer traces; never infer PWM from telemetry alone."""
from pathlib import Path
import re

def validate(path, case):
    symbols = {}
    values = {}
    active = set()
    aux_seen = set()
    pwm_levels = {i:set() for i in range(4)}
    enabled = False
    def inspect():
        nonlocal enabled
        if values.get(4) != '1': return
        enabled = True
        if any(values.get(i) not in {'0','1'} for i in range(7)):
            raise ValueError('Unknown control level while EN is high')
        if values.get(0) == values.get(1) == '1' or values.get(2) == values.get(3) == '1':
            raise ValueError('Opposing wheel PWM signals active while EN is high')
        active.update(i for i in range(4) if values.get(i)=='1')
        for i in range(4): pwm_levels[i].add(values[i])
        aux_seen.update(i for i in (5,6) if values.get(i)=='1')
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith('$var '):
            fields = line.split()
            match = re.fullmatch(r'D([0-7])',fields[4])
            if match: symbols[fields[3]]=int(match[1])
        elif line.startswith('#'):
            inspect() # Inspect the final signal levels for each timestamp.
        elif line and line[0] in '01xXzZ' and line[1:] in symbols:
            values[symbols[line[1:]]]=line[0].lower()
        elif line.startswith('b'):
            fields=line.split()
            if len(fields)==2 and fields[1] in symbols:
                values[symbols[fields[1]]]=fields[0][1:].lower()
    inspect()
    if len(symbols)!=8: raise ValueError('Expected all eight logic-analyzer D0-D7 channels in VCD')
    expected = {'auto_left':{1,2},'auto_right':{0,3},'obstacle_no_path':set()}.get(case,{0,2})
    if active != expected: raise ValueError(f'Wheel PWM channels observed {active}, expected {expected}')
    if any(pwm_levels[i] != {'0','1'} for i in expected):
        raise ValueError('Expected wheel channel did not show both PWM levels with EN asserted')
    if case=='obstacle_no_path' and enabled: raise ValueError('EN unexpectedly asserted in blocked scene')
    expected_aux = {'brushes_only':{5},'conveyor_only':{6},'emergency_and_reset':{5,6}}.get(case,set())
    if aux_seen != expected_aux: raise ValueError(f'Auxiliary channels observed {aux_seen}, expected {expected_aux}')
    return {'wheel_pwm_channels':sorted(active),'aux_channels':sorted(aux_seen),'interlock':'PASS'}
