#!/usr/bin/env python3
"""Static source/diagram contracts; these checks do not execute Wokwi."""
from pathlib import Path
import json
import re
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root/'scripts/sync_wokwi.py'), '--check'], check=True)
pins = dict((name,int(value)) for name,value in re.findall(r'(\w+)\s*=\s*(\d+)',(root/'include/rover_pins.h').read_text()))
expected = dict(L_FWD=16,L_REV=17,R_FWD=18,R_REV=19,TF=32,EF=34,TL=33,EL=35,TR=13,ER=36,
                BRUSH_IN1=21,BRUSH_IN2=22,CONVEYOR_IN3=23,CONVEYOR_IN4=25,ENABLE=14,ESTOP_OK=27)
assert pins == expected, 'GPIO contract changed: update firmware, diagram and physical wiring together'
assert len(set(pins.values())) == len(pins), 'Duplicate GPIO assignments'
assert all(value in {34,35,36} for name,value in pins.items() if name in {'EF','EL','ER'})
assert all(value not in {0,2,5,12,15,1,3,6,7,8,9,10,11,34,35,36,39} for name,value in pins.items() if name not in {'EF','EL','ER'})
d = json.loads((root/'wokwi/diagram.json').read_text())
parts = {p['id']:p for p in d['parts']}
assert len(parts)==len(d['parts']), 'Duplicate part IDs'
assert not any('resistor' in p['type'].lower() for p in parts.values()), 'Resistors are forbidden in this Wokwi model'
edges = {frozenset(c[:2]) for c in d['connections']}
def connected(a,b): assert frozenset((a,b)) in edges, f'Missing {a} -> {b}'
def esp(name): return 'esp:'+{16:'RX2',17:'TX2',36:'VP'}.get(pins[name],'D'+str(pins[name]))
for sensor,t,e in [('front','TF','EF'),('left','TL','EL'),('right','TR','ER')]:
    connected(sensor+':TRIG',esp(t)); connected(sensor+':ECHO',esp(e))
    connected(sensor+':VCC','esp:VIN'); connected(sensor+':GND','esp:GND.1')
# Both brush indicators must share channel A; conveyor must use channel B.
for i,name in enumerate(('L_FWD','L_REV','R_FWD','R_REV','BRUSH_IN1','BRUSH_IN1','CONVEYOR_IN3')):
    connected(esp(name),f'out{i}:A'); connected(f'out{i}:C','esp:GND.2')
connected(esp('ENABLE'),'enable_led:A'); connected('enable_led:C','esp:GND.2')
connected(esp('ESTOP_OK'),'estop:2'); connected('esp:3V3','estop:1'); connected('esp:GND.1','estop:3')
for i,name in enumerate(('L_FWD','L_REV','R_FWD','R_REV','ENABLE','BRUSH_IN1','CONVEYOR_IN3','ESTOP_OK')):
    connected(esp(name),f'logic:D{i}')
connected('logic:GND','esp:GND.1')
for c in d['connections']:
    assert all(s.split(':')[0] in parts for s in c[:2]), f'Unknown part in {c}'
    assert not any(s in {'esp:D26','esp:VN'} for s in c[:2]), 'Obsolete GPIO26/39 connection'
print(f'PASS: {len(pins)} unique supported GPIOs; one L298N; shared brushes; independent conveyor; no resistors; E-stop and analyzer match')
