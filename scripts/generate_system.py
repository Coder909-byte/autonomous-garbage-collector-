#!/usr/bin/env python3
"""Additive system overlay. E2 files and W001-W201 remain unchanged.
Uses the established vector/PDF/PNG Drawing renderer; no physical approval.
"""
from pathlib import Path
import copy,csv,hashlib,json
from generate_wiring import Drawing as BaseDrawing,csvwrite
def Drawing(title,subtitle):return BaseDrawing(title,subtitle,revision="S1",date="10 Nov 2026")
ROOT=Path(__file__).resolve().parents[1]

def load():
    overlay=json.loads((ROOT/'electrical/system_design.json').read_text())
    for p,digest in overlay['base_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest, 'E2 base changed: '+p
    model=json.loads((ROOT/'electrical/design.json').read_text())
    assert set(overlay['components']) & set(model['components']) == {'CAM1'}
    assert model['components']['CAM1']['kind']=='reserved'
    rows=list(csv.DictReader((ROOT/'electrical/connections.csv').open()))
    components={**model['components'],**overlay['components']}
    pins={node:n['name'] for n in model['nets'] for node in n['nodes']}
    used={r['wire_id'] for r in rows}
    for wire in overlay['connections']:
        assert wire['wire_id'] not in used;used.add(wire['wire_id'])
        for node in (wire['source'],wire['destination']):
            ref,pin=node.split('.',1)
            assert ref in components and pin in components[ref]['pins'], 'Unknown functional port '+node
            assert pins.get(node,wire['net'])==wire['net'], 'Cross-net connection '+node
            pins[node]=wire['net']
        rows.append(wire)
    for ref,c in overlay['components'].items():
        assert all(ref+'.'+p in pins or ref+'.'+p in overlay['no_connect'] for p in c['pins']), 'Missing system port '+ref
    return overlay,model,rows

def generate():
    o,base,rows=load();csvwrite(ROOT/'electrical/system_connections.csv',rows)
    aggregate=copy.deepcopy(base);aggregate['revision']=o['revision'];aggregate['components'].update(o['components'])
    nets={n['name']:n for n in aggregate['nets']}
    for r in o['connections']:
        n=nets.get(r['net'])
        if n is None:
            n={'name':r['net'],'kind':r['signal_type'],'nodes':[],'voltage':r['voltage'],'status':r['status'],'protection':r['protection'],'verify':r['verification']};aggregate['nets'].append(n);nets[n['name']]=n
        for node in [r['source'],r['destination']]:
            if node not in n['nodes']:n['nodes'].append(node)
    for node in list(aggregate['no_connect']):
        if any(node in n['nodes'] for n in aggregate['nets']): del aggregate['no_connect'][node]
    aggregate['no_connect'].update(o['no_connect'])
    aggregate['communication_links']=o['communication_links'];aggregate['physical_release']='HOLD'
    (ROOT/'electrical/system_netlist.json').write_text(json.dumps(aggregate,indent=2)+'\n')
    d=Drawing('Rover full-system architecture / S1','Control and video are independent. E2 electrical package remains authoritative for W001-W201; camera additions W202-W211.')
    d.card(65,165,425,140,'LAPTOP / local operator',['React / TypeScript dashboard','Loopback Node bridge; one serial owner','No automatic ARM or restart'])
    d.card(620,165,455,140,'ESP1 / main ESP32',['USB serial 115200 baud','Motor / sensor / safety authority','16 E2 GPIO assignments unchanged'])
    d.line([(490,225),(620,225)],'#1565c0',3);d.text(505,212,'USB data',13)
    d.card(1200,165,420,140,'CAM1 / separate ESP32-CAM',['Supported AI-Thinker config only','Actual module identity PENDING','MJPEG :81 / HTTP status :80'],True)
    d.line([(280,165),(280,145),(1410,145),(1410,165)],'#23844b',2,True);d.text(620,137,'Trusted local Wi-Fi: camera video / snapshots only',13)
    d.card(65,385,425,175,'POWER / existing E2',['BT1 -> F0 -> S0 -> P1 -> TB_POS','F1 / BUCK1 / OV1 -> ESP1','F2 / BUCK2 / OV2 -> logic + sensors','Dedicated star returns -> TB_GND'],True)
    d.card(620,385,455,175,'CONTROL / E2 interfaces',['U1 AHCT: PWM + TRIG + gated EN','U2 LVC: three protected ECHO inputs','3 x HC-SR04: front / left / right','GPIO27: active-HIGH healthy feedback'],True)
    d.card(1200,385,420,175,'NEW camera power branch',['TB_POS -> F3 -> BUCK3 -> OV3','Protected regulated 5V -> CAM1','Separate return; C_CAM bypass','W202-W211; current/thermal HOLD'],True)
    d.line([(490,465),(620,465)],'#c62828',3);d.line([(845,305),(845,385)],'#1565c0',2)
    d.line([(490,545),(550,545),(550,600),(1410,600),(1410,560)],'#c62828',3,True)
    d.line([(1410,385),(1410,305)],'#c62828',3,True)
    d.card(65,680,425,180,'INDEPENDENT PHYSICAL STOP',['S2: 3 isolated NC contacts','OV1/OV2 -> coil permissives','S3 hardware arm + K1 seal-in','K1 opens motor bus; EN opens too','Software ESTOP does not open K1'],True)
    d.card(620,680,455,180,'DRIVERS / motor branch',['K1 -> FL / FR / FA','2 x BTS7960 -> M1-M4 wheels','1 x conditional L298N -> M5/M6/M7','FM1-FM7 per motor; grounds E2','No driver load approval'],True)
    d.card(1200,680,420,180,'SAFETY / commissioning',['Startup DISARMED, EN low','1200ms firmware manual timeout','Browser lease 300ms; release = S','Actual USB supply isolation HOLD','Physical verification NOT performed'])
    d.line([(845,560),(845,680)],'#1565c0',3);d.line([(490,765),(620,765)],'#c62828',4)
    d.lines(65,945,'Grounds: retain E2 star architecture and dedicated motor returns. Camera return routes via BUCK3 to TB_GND, never through ESP1 or laptop. Do not parallel any positive regulator output. Camera power stays independent of K1 and cannot energize a motor output.',width=185,size=14,leading=24)
    d.lines(65,1030,'All blocks with dashed borders remain hardware HOLD. Generic ports are functions awaiting actual part selection, not manufacturer terminal numbers. Existing E2 sheets retain all resistor, fuse, motor and control-wire detail; the next sheet contains every new camera connection.',width=185,size=14,leading=24)
    d.save('system_architecture')
    d=Drawing('Camera protected-power wiring / S1','Additive connection sheet. All source and destination ports below are functional until exact hardware identification and mapping.')
    for i,r in enumerate(o['connections']):
        y=172+i*70
        d.svg.append(f'<g data-wire-id="{r["wire_id"]}" data-source="{r["source"]}" data-destination="{r["destination"]}">')
        d.text(60,y,r['wire_id'],16,bold=True);d.text(165,y,r['source']+' -> '+r['destination'],17,bold=True)
        d.text(165,y+22,r['net']+' | '+r['connection_kind']+' | '+r['voltage'],13)
        d.text(165,y+42,r['protection'],12,color='#995b00');d.svg.append('</g>')
    d.lines(65,925,'BUCK3 IN-/OUT- bond W205 is an internal continuity inspection, never an extra jumper. Camera power return is dedicated to this branch. No physical ESP1 GPIO connection to CAM1. Laptop camera connection is Wi-Fi only; programmer is a separate temporary isolated setup.',width=185,size=14,leading=23)
    d.lines(65,1015,'Provisional allocation only: 5V x 1A = 5W continuous; 5V x 2A = 10W transient envelope. At assumed 80% efficiency: 6.25W / 12.5W input; losses 1.25W / 2.5W. These are design assumptions, not camera measurements or regulator qualification. Fuse current/thermal values remain TBD.',width=185,size=14,leading=23)
    d.save('camera_power')
    result={'revision':o['revision'],'base_connections':201,'added_connections':len(o['connections']),'total_connections':len(rows),'physical_release':'HOLD','drawings':['system_architecture','camera_power']}
    (ROOT/'electrical/system_manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':generate()
