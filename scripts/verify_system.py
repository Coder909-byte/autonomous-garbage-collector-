#!/usr/bin/env python3
"""Reproducible software-only verification. Never opens serial or uploads hardware."""
from pathlib import Path
import datetime,json,os,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'artifacts/system';out.mkdir(parents=True,exist_ok=True)
pio=r/'.venv/bin/pio';python=r/'.venv/bin/python'
commands=[
 ('baseline-regression',[str(python),'scripts/verify.py']),
 ('simulation-camera-host',['python3','scripts/build_simulator.py']),
 ('typescript-tests',['npm','test']),
 ('laptop-build',['npm','run','build']),
 ('production-smoke',['node','scripts/smoke_production.mjs']),
 ('camera-build',[str(pio),'run','-d','camera']),
 ('system-graph',[str(python),'scripts/check_system.py']),
 ('frozen-handover',[str(python),'scripts/check_team_handover.py']),
 ('browser-tests',['npm','run','test:e2e']),
 ('dependency-audit',['npm','audit','--json','--registry=https://registry.npmjs.org']),
]
results=[]
for name,args in commands:
 print('Running '+name,flush=True)
 with (out/(name+'.log')).open('w') as log:
  p=subprocess.run(args,cwd=r,stdout=log,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':args,'exit_code':p.returncode,'log':str((out/(name+'.log')).relative_to(r))})
 print(name+(': PASS' if p.returncode==0 else ': FAILED'),flush=True)
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'working_tree':subprocess.check_output(['git','status','--short'],cwd=r,text=True).splitlines(),'hardware_used':False,'firmware_uploaded':False,'physical_release':'HOLD','checks':results}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
sys.exit(1 if any(x['exit_code'] for x in results) else 0)
