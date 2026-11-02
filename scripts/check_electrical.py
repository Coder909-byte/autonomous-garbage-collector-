#!/usr/bin/env python3
"""Structural electrical checks. Not KiCad ERC, SPICE, component approval or physical verification."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def check(d):
    comps=d['components']; nets={n['name']:n for n in d['nets']}
    assert len(nets)==len(d['nets']), 'Duplicate net name'
    assigned={}
    for name,n in nets.items():
        assert len(n['nodes'])>=2, 'Floating net '+name
        assert len(set(n['nodes']))==len(n['nodes']), 'Duplicate node '+name
        assert n['status'] in {'PROVISIONAL','BLOCKED_MISSING','BLOCKED_RATING'}, 'Unreviewed approval status'
        for node in n['nodes']:
            ref,pin=node.split('.',1)
            assert ref in comps and pin in comps[ref]['pins'], 'Unknown pin '+node
            assert node not in assigned, 'Pin on multiple nets '+node
            assigned[node]=name
    for ref,c in comps.items():
        assert c['footprint'] is None, 'Unverified footprint assigned'
        for pin in c['pins']:
            node=ref+'.'+pin
            assert (node in assigned) != (node in d['no_connect']), 'Missing/contradictory pin disposition '+node
    pins=dict((k,int(v)) for k,v in re.findall(r'(\w+)\s*=\s*(\d+)',(ROOT/'include/rover_pins.h').read_text()))
    assert set(pins)==set(d['gpio_bindings']), 'Missing firmware GPIO in electrical model'
    assert len(set(pins.values()))==len(pins)
    for name,b in d['gpio_bindings'].items():
        assert pins[name]==b['gpio'], 'GPIO mismatch '+name
        assert assigned[b['endpoint']]==b['net'], 'GPIO on wrong net '+name
        if 'buffer_in' in b:
            assert assigned['U1.'+b['buffer_in']]==name+'_3V3'
            assert assigned['U1.'+b['buffer_out']]==name+'_5V'
    def same(net,*nodes): assert all(assigned.get(n)==net for n in nodes), (net,nodes)
    assert len([c for c in comps if c.startswith('M') and c[1:].isdigit()])==7
    assert len([c for c in comps if c.startswith('DRV_')])==3
    for name,gpio,top,bottom,sensor in [('EF',34,23,24,'US_F'),('EL',35,25,26,'US_L'),('ER',36,27,28,'US_R')]:
        same(name+'_RAW',sensor+'.ECHO',f'R{top}.1')
        same(name+'_SAFE',f'ESP1.GPIO{gpio}',f'R{top}.2',f'R{bottom}.1')
        same('GND',f'R{bottom}.2')
        assert comps['R'+str(top)]['value'].startswith('2.2k 1%')
        assert comps['R'+str(bottom)]['value'].startswith('3.3k 1%')
        assert nets[name+'_SAFE']['status']=='BLOCKED_MISSING'
    # No raw sensor, 5V control, battery or motor-output net may touch a GPIO.
    gpio_nets={b['net'] for b in d['gpio_bindings'].values()}
    for node,n in assigned.items():
        if node.startswith('ESP1.GPIO'): assert n in gpio_nets
    for ref,out_a,out_b in [('DRV_L','M+','M-'),('DRV_R','M+','M-'),('DRV_A','OUT1','OUT2')]:
        group={'DRV_L':(1,2),'DRV_R':(3,4),'DRV_A':(5,6)}[ref]
        for i in group:
            assert assigned[ref+'.'+out_a]==assigned[f'FM{i}.IN']
            assert assigned[ref+'.'+out_b]==assigned[f'M{i}.B']
            assert assigned[f'FM{i}.OUT']==assigned[f'M{i}.A']
    assert assigned['DRV_A.OUT3']==assigned['FM7.IN']
    assert assigned['DRV_A.OUT4']==assigned['M7.B']
    same('EN_DRIVER_5V','S2.EN_NC','DRV_L.R_EN','DRV_L.L_EN','DRV_R.R_EN','DRV_R.L_EN','DRV_A.ENA','DRV_A.ENB')
    assert sum(n.startswith('DRV_') for n in nets['EN_DRIVER_5V']['nodes'])==6
    for i in range(13,19): same('EN_DRIVER_5V',f'R{i}.1'); same('GND',f'R{i}.2')
    same('ENABLE_3V3','ESP1.GPIO14','R5.1'); assert comps['R5']['value'].startswith('2.2k')
    same('GND','R5.2','R29.2'); same('ESTOP_OK','K1.AUX_SENSE_NO','ESP1.GPIO27','R29.1')
    same('SENSE_STOP_OK','S2.SENSE_NC','K1.AUX_SENSE_COM')
    same('COIL_STOP_CHAIN','S2.COIL_NC','S3.COM','K1.AUX_HOLD_COM')
    same('COIL_HOLD','S3.NO','K1.AUX_HOLD_NO','K1.A1')
    same('COIL_FUSED','FK.OUT','OV1.PG_COM'); same('COIL_PG1','OV1.PG_NO','OV2.PG_COM')
    same('COIL_PG2','OV2.PG_NO','S2.COIL_COM')
    same('MOTOR_SWITCHED','K1.MAIN_NO','FL.IN','FR.IN','FA.IN')
    for clamp,rail in [('Z_L','LEFT_SUPPLY'),('Z_R','RIGHT_SUPPLY'),('Z_A','AUX_SUPPLY')]:
        same(rail,clamp+'.+');same('GND',clamp+'.-')
    for i,rail in ((1,'V5_MCU'),(2,'V5_LOGIC')):
        same(rail+'_RAW',f'BUCK{i}.OUT+',f'OV{i}.IN+')
        same(rail,f'OV{i}.OUT+')
    assert assigned['BUCK1.OUT+']!=assigned['BUCK2.OUT+']
    assert assigned['DRV_L.B+']=='LEFT_SUPPLY' and assigned['DRV_R.B+']=='RIGHT_SUPPLY'
    assert assigned['DRV_A.Vs_12V']=='AUX_SUPPLY'
    for ref in ('F0','FL','FR','FA','F1','F2','FK')+tuple('FM'+str(i) for i in range(1,8)):
        assert 'TBD' in comps[ref]['value'], 'Unsupported fuse rating invented'
    # Bounds assume ECHO high follows the qualified 4.75-5.25V rail.
    low=4.75*(3300*.99)/(2200*1.01+3300*.99)
    high=5.25*(3300*1.01)/(2200*.99+3300*1.01)
    assert low>0.75*3.3 and high<3.3
    return {'components':len(comps),'nets':len(nets),'connected_pins':len(assigned),'no_connect_pins':len(d['no_connect']),
            'gpio_assignments':len(pins),'divider_assumed_high_bounds_V':[round(low,3),round(high,3)],
            'enable_pulldown_load_mA':3.0,'result':'PASS - structural only; all physical connections remain unapproved'}
if __name__=='__main__':
    print(json.dumps(check(json.loads((ROOT/'electrical/design.json').read_text())),indent=2))
