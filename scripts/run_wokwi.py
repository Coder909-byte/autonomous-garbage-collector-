#!/usr/bin/env python3
"""Prepare/run signal-level Wokwi scenarios. Never accesses physical serial ports."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from check_vcd import validate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/wokwi-scenarios'

def state(motion, brush=0, conveyor=0):
    return {'wait-serial': f'STATE motion={motion} en={int(motion != "STOPPED")} brush={brush} conveyor={conveyor}'}

def command(text, accepted=True):
    return [{'write-serial': text+'\n'}, {'wait-serial': ('OK ' if accepted else 'ERR ')+text}]

def pin(name,value):
    return {'expect-pin': {'part-id':'esp','name':name,'value':value}}

def aux(text, brush, conveyor):
    # Applied-state telemetry is emitted before the command acknowledgement.
    return [{"write-serial":text+"\n"}, state("FORWARD",brush,conveyor), {"wait-serial":"OK "+text}]

def all_stopped():
    return [pin(p,0) for p in ('D14','RX2','TX2','D18','D19','D21','D22','D23','D25')]

def forward():
    return command('ARM') + command('F') + [state('FORWARD'),pin('D14',1),pin('TX2',0),pin('D19',0)]

def cases():
    return [
        ('auto_forward', (100,100,100), command('ARM')+command('AUTO')+
         [state('FORWARD'),pin('D14',1),pin('TX2',0),pin('D19',0)]),
        ('auto_left', (20,100,60), command('ARM')+command('AUTO')+
         [state('LEFT'),pin('D14',1),pin('RX2',0),pin('D19',0),pin('D21',0),pin('D23',0)]),
        ('auto_right', (20,60,100), command('ARM')+command('AUTO')+
         [state('RIGHT'),pin('D14',1),pin('TX2',0),pin('D18',0),pin('D21',0),pin('D23',0)]),
        ('obstacle_no_path', (20,45,45), command('ARM')+command('AUTO')+[{'delay':'900ms'}]+all_stopped()),
        ('emergency_and_reset', (100,100,100), forward()+aux('CLEAN ON',1,1)+command('ESTOP')+all_stopped()+command('ARM',False)+
         command('RESET')+all_stopped()+command('ARM')+all_stopped()+command('F')+
         [state('FORWARD')]+command('STOP')+all_stopped()+command('ARM',False)),
        ('brushes_only', (100,100,100), forward()+aux('BRUSH ON',1,0)+
         [pin('D21',1),pin('D22',0),pin('D23',0),pin('D25',0)]+
         aux('BRUSH OFF',0,0)+command('S')+all_stopped()),
        ('conveyor_only', (100,100,100), forward()+aux('CONVEYOR ON',0,1)+
         [pin('D21',0),pin('D22',0),pin('D23',1),pin('D25',0)]+
         aux('CONVEYOR OFF',0,0)+command('S')+all_stopped()),
        ('manual_deadman', (100,100,100), forward()+[state('STOPPED')]+all_stopped()),
    ]

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    diagram = json.loads((ROOT/'wokwi/diagram.json').read_text())
    for name, distances, steps in cases():
        folder = OUT/name
        folder.mkdir(exist_ok=True)
        scene = json.loads(json.dumps(diagram))
        for part in scene['parts']:
            if part['id'] in ('front','left','right'):
                part['attrs']['distance'] = str(distances[('front','left','right').index(part['id'])])
        (folder/'diagram.json').write_text(json.dumps(scene,indent=2)+'\n')
        binary = ROOT/'.pio/build/esp32dev/firmware.bin'
        elf = ROOT/'.pio/build/esp32dev/firmware.elf'
        (folder/'wokwi.toml').write_text('[wokwi]\nversion = 1\nfirmware = '+json.dumps(str(binary))+'\nelf = '+json.dumps(str(elf))+'\n')
        scenario = {'name':name,'version':1,'author':'Rover software validation',
                    'steps':[{'wait-serial':'READY DISARMED'},{'wait-serial':'DIST'}]+steps+[{'delay':'120ms'}]}
        # JSON is valid YAML and avoids an extra YAML-generation dependency.
        (folder/'scenario.yaml').write_text(json.dumps(scenario,indent=2)+'\n')
    print(f'Prepared {len(cases())} Wokwi scenarios in {OUT}')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    args = parser.parse_args()
    prepare()
    if args.prepare_only:
        print('PREPARED ONLY: no simulation has been executed.')
        return 0
    cli = shutil.which('wokwi-cli') or str(ROOT/'.tools/wokwi-cli')
    missing = []
    if not os.getenv('WOKWI_CLI_TOKEN'): missing.append('WOKWI_CLI_TOKEN is not configured')
    if not Path(cli).is_file(): missing.append('Wokwi CLI is not installed')
    if not (ROOT/'.pio/build/esp32dev/firmware.bin').is_file(): missing.append('ESP32 firmware must be built first')
    report = {'scope':'Wokwi digital control signals only; no mechanical/power-electronics model','cases':{}}
    if missing:
        report['status']='NOT EXECUTED'
        report['reason']='; '.join(missing)
        report['cases']={name:{'status':'NOT EXECUTED'} for name,_,_ in cases()}
        (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('NOT EXECUTED: '+report['reason'])
        return 2
    for name,_,_ in cases():
        folder = OUT/name
        args = [cli,str(folder),'--scenario',str(folder/'scenario.yaml'),'--timeout','15000',
                '--vcd-file',str(folder/'logic.vcd')]
        with (folder/'runtime.log').open('w') as log:
            result = subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        entry = {'status':'FAIL','cli_exit_code':result.returncode}
        if result.returncode==0:
            try:
                entry['vcd']=validate(folder/'logic.vcd',name)
                entry['status']='PASS'
            except (OSError,ValueError) as error:
                entry['reason']=str(error)
        report['cases'][name]=entry
        print(name+': '+entry['status'],flush=True)
    report['status']='PASS' if all(entry['status']=='PASS' for entry in report['cases'].values()) else 'FAIL'
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    sys.exit(main())
