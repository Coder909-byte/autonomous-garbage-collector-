#!/usr/bin/env python3
"""Validate additive system graph and camera wire traceability; no hardware claims."""
from pathlib import Path
import csv,json,copy,sys
import xml.etree.ElementTree as ET
from generate_system import load
ROOT=Path(__file__).resolve().parents[1]

def check(model,rows):
    original=json.loads((ROOT/'electrical/design.json').read_text())
    for ref,c in original['components'].items():
        if ref!='CAM1': assert model['components'][ref]==c,'E2 component changed '+ref
    assert model['gpio_bindings']==original['gpio_bindings']
    nodes={};nets={n['name']:n for n in model['nets']}
    for n in model['nets']:
        for node in n['nodes']:
            ref,pin=node.split('.',1)
            assert pin in model['components'][ref]['pins']
            assert node not in nodes,'Short/multiple net '+node
            nodes[node]=n['name']
    for ref,c in model['components'].items():
        for pin in c['pins']:
            node=ref+'.'+pin;assert (node in nodes)!=(node in model['no_connect']), 'Undisposed pin '+node
    for n in original['nets']:
        assert set(n['nodes'])<=set(nets[n['name']]['nodes']),'E2 net changed '+n['name']
    expect={'F3.IN':'PACK_PROTECTED','F3.OUT':'CAMERA_INPUT','BUCK3.IN+':'CAMERA_INPUT','BUCK3.IN-':'GND','BUCK3.OUT-':'GND','BUCK3.OUT+':'V5_CAMERA_RAW','OV3.IN+':'V5_CAMERA_RAW','OV3.OUT+':'V5_CAMERA','OV3.GND':'GND','CAM1.5V':'V5_CAMERA','CAM1.GND':'GND','C_CAM.1':'V5_CAMERA','C_CAM.2':'GND'}
    assert all(nodes[p]==n for p,n in expect.items()),'Camera protection/ground/rail topology changed'
    assert 'CAM1.U0R' in model['no_connect'] and 'CAM1.U0T' in model['no_connect']
    seen=set();graph={}
    for row in rows:
        wire=row['wire_id'];assert wire not in seen;seen.add(wire)
        a,b=row['source'].split()[0],row['destination'].split()[0]
        assert nodes[a]==nodes[b]==row['net'],'Cross-net conductor '+wire
        graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    for n in model['nets']:
        reached=set();todo=[n['nodes'][0]]
        while todo:
            a=todo.pop()
            if a not in reached:reached.add(a);todo.extend(graph.get(a,set())-reached)
        assert reached==set(n['nodes']), 'Disconnected '+n['name']
    assert len(rows)==211
    assert sum(r['connection_kind']=='INTERNAL_VERIFY' for r in rows)==5
    return True

def main():
    o,base,expected=load();model=json.loads((ROOT/'electrical/system_netlist.json').read_text())
    rows=list(csv.DictReader((ROOT/'electrical/system_connections.csv').open()))
    assert expected==rows,'Stale aggregate export'
    check(model,rows)
    base_rows=list(csv.DictReader((ROOT/'electrical/connections.csv').open()))
    assert rows[:201]==base_rows
    svg=ET.parse(ROOT/'docs/diagrams/camera_power.svg').getroot()
    found={e.attrib['data-wire-id']:(e.attrib['data-source'],e.attrib['data-destination']) for e in svg.iter() if 'data-wire-id' in e.attrib}
    assert found=={r['wire_id']:(r['source'],r['destination']) for r in rows[201:]}
    print('PASS: S1 211 records (206 external, 5 internal checks); all 201 E2 rows preserved; camera protected branch and diagram match. Physical HOLD.')
if __name__=='__main__':main()
