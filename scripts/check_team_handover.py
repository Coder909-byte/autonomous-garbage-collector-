#!/usr/bin/env python3
"""Validate the handover against frozen E2 inputs. No hardware compatibility claim."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import subprocess

from pypdf import PdfReader
from electrical_export_contracts import check_classic_pdf_xref
from generate_team_handover import ROOT, DATA, PDF, AUTHORITIES, plain, section_for, buy_now


def read_csv(path):
    with path.open() as f:return list(csv.DictReader(f))


def norm(text):
    return re.sub(r'\s+','',plain(text))


def validate_records(source,records):
    ids=[r['wire_id'] for r in records]
    assert len(ids)==len(set(ids)), 'Duplicate handover record'
    assert set(ids)=={r['wire_id'] for r in source}, 'Missing/extra E2 connection'
    actual={r['wire_id']:r for r in records}
    for r in source:
        a=actual[r['wire_id']]
        for key,value in r.items():assert a[key]==value, 'Canonical field changed: '+r['wire_id']+' / '+key
        assert int(a['handover_section'])==section_for(r), 'Connection in wrong section'
        assert 'UNPOWERED FIRST' in a['team_verification_method'], 'Missing unpowered verification boundary'
        assert r['verification'] in a['team_verification_method'], 'E2 verification omitted'
        assert r['protection'] in a['intermediate_components'] or r['connection_kind']=='INTERNAL_VERIFY', 'Protection omitted'
        if r['connection_kind']=='INTERNAL_VERIFY':
            assert a['action']=='INSPECT EXISTING BOND - DO NOT ADD WIRE', 'Internal bond converted into added wire'
            assert 'NO WIRE TO ADD' in a['intermediate_components']
            assert a['required_electrical_rating'].startswith('N/A:'), 'Internal bond given new conductor rating'
        else:
            assert a['action']=='EXTERNAL CONNECTION - gate dependent'
            assert r['voltage'] in a['required_electrical_rating'], 'Expected voltage omitted'
            assert r['conductor_class'] in a['required_electrical_rating'], 'Conductor requirement omitted'
    return actual


def check():
    plan=json.loads((DATA/'plan.json').read_text());manifest=json.loads((DATA/'manifest.json').read_text())
    model=json.loads((ROOT/'electrical/design.json').read_text())
    source=read_csv(ROOT/'electrical/connections.csv');records=read_csv(DATA/'TEAM_CONNECTION_REGISTER.csv')
    actual=validate_records(source,records)
    assert len(records)==201
    internal=[r['wire_id'] for r in records if r['connection_kind']=='INTERNAL_VERIFY']
    assert internal==['W042','W044','W046','W048'] and len(records)-len(internal)==197
    for p,digest in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,'Stale handover input '+p
    for p in AUTHORITIES:
        baseline=subprocess.check_output(['git','show',plan['baseline_commit']+':'+p],cwd=ROOT)
        # E2's .gitattributes normalizes CSV/text to LF in Git; the existing
        # working CSV exports use CRLF. Compare content using Git's convention.
        assert (ROOT/p).read_bytes().replace(b'\r\n',b'\n')==baseline.replace(b'\r\n',b'\n'),'Authoritative E2 input modified '+p
    pin_source=(ROOT/'include/rover_pins.h').read_text()
    pins={name:int(value) for name,value in re.findall(r'(\w+)\s*=\s*(\d+)',pin_source)}
    assert {name:b['gpio'] for name,b in model['gpio_bindings'].items()}==pins
    assert len(set(pins.values()))==16
    expected_purchases=buy_now(model);purchases=read_csv(DATA/'PURCHASE_NOW.csv')
    assert len(purchases)==len(expected_purchases)
    for a,b in zip(purchases,expected_purchases):
        assert a=={k:str(v) for k,v in b.items()}, 'Purchase-now value/count mismatch'
    assert sum(int(r['quantity']) for r in purchases if 'resistor' in r['item'])==32
    assert sum(int(r['quantity']) for r in purchases if 'capacitor' in r['item'])==5
    purchase_md=(ROOT/'docs/FINAL_PURCHASE_LIST.md').read_text()
    assert all(model['components'][ref]['value'] in purchase_md for ref in ('U1','U2'))
    assert [s['number'] for s in plan['sections']]==list(range(1,14))
    assert [c['id'] for c in plan['checkpoints']]==list('ABCDEFGHIJ')
    assert all(all(c.get(k) for k in ('prerequisites','instructions','photos','measurements','pass','stop','send')) for c in plan['checkpoints'])
    for cp in plan['checkpoints'][5:]:assert 'NOT RELEASED' in cp['state']
    assert 'I motor-free cutoff test must PASS' in plan['checkpoints'][7]['prerequisites']
    worksheet=read_csv(DATA/'TEAM_ASSEMBLY_RECORD.csv');validate_ids={r['wire_id'] for r in worksheet}
    assert validate_ids==set(actual) and len(worksheet)==201
    assert all(r['status']=='PENDING' and not r['measured_value'] for r in worksheet), 'Fabricated physical measurement'
    checkpoint_records=read_csv(DATA/'TEAM_CHECKPOINT_RECORD.csv')
    assert all(r['result']=='PENDING' for r in checkpoint_records)
    i_records=[r for r in checkpoint_records if r['checkpoint']=='I']
    assert len(i_records)==2 and {r['motor_free_or_loaded_I'].split(' - ')[0] for r in i_records}=={'MOTOR-FREE PREFLIGHT','LOADED CONFIRMATION'}
    assert all(r['result']=='PENDING' for r in read_csv(DATA/'TEAM_MEASUREMENT_RECORD.csv'))
    photos=json.loads((DATA/'photo_inventory.json').read_text())
    assert photos==manifest['photo_inventory']
    if not photos['files']:
        assert not photos['visible_terminal_observations'] and not photos['actual_terminal_matches'], 'Invented photograph match'
    for p in photos['files']:assert (ROOT/p).is_file()
    check_classic_pdf_xref(PDF.read_bytes());reader=PdfReader(PDF,strict=True)
    assert hashlib.sha256(PDF.read_bytes()).hexdigest()==manifest['pdf_sha256']
    assert len(reader.pages)==manifest['pdf_pages']==len(manifest['page_roles'])
    texts=[p.extract_text() for p in reader.pages]
    assert all(len(t)>100 for t in texts), 'Blank/unreadable PDF page'
    counts=Counter();pdf_record_pages={}
    for page_no,text in enumerate(texts,1):
        matches=list(re.finditer(r'Record\s+(W\d{3})\b',text))
        for i,match in enumerate(matches):
            wire=match[1];counts[wire]+=1;pdf_record_pages[wire]=page_no
            end=matches[i+1].start() if i+1<len(matches) else len(text)
            block=norm(text[match.start():end]);r=actual[wire]
            for key in ('source','destination','color','net','action','intermediate_components','required_electrical_rating','team_verification_method','status'):
                assert norm(r[key]) in block, 'PDF record field missing or split: '+wire+' / '+key
            assert int(r['pdf_page'])==page_no
    assert set(counts)==set(actual) and all(v==1 for v in counts.values()), 'Detailed record duplicated/missing in PDF'
    assert all(str(page_no) in texts[0] for page_no in manifest['section_starts'].values())
    purchase_text=norm(' '.join(texts[manifest['section_starts']['12']-1:manifest['section_starts']['13']-1]))
    for p in purchases:
        assert norm(p['item']) in purchase_text and norm(p['references']) in purchase_text, 'Fixed purchase selection missing from PDF'
    purchase_lines=[line for line in purchase_md.splitlines() if line.startswith('|')][2:]
    for line in purchase_lines:
        for field in [v.strip() for v in line.strip('|').split('|')]:
            visible=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',field).replace('**','').replace('`','')
            assert norm(visible) in purchase_text, 'E2 purchase requirement missing from PDF: '+visible
    diagram_pages=0
    for role in manifest['page_roles']:
        if role['role']!='E2 diagram':continue
        src=PdfReader(ROOT/role['source'],strict=True).pages[role['source_page']-1].extract_text()
        assert norm(src) in norm(texts[role['page']-1]), 'Existing E2 diagram text changed'
        diagram_pages+=1
    assert len(reader.outline)>=13
    assert set(reader.attachments)=={'TEAM_ASSEMBLY_RECORD.csv','TEAM_CHECKPOINT_RECORD.csv'}
    return {'result':'PASS - handover consistency only; physical compatibility NOT VERIFIED',
            'baseline_commit':plan['baseline_commit'],'e2_authorities_unchanged':len(AUTHORITIES),
            'baseline_comparison':'Git LF-normalized text; original working-file hashes also recorded',
            'pdf_pages':len(reader.pages),'sections':13,'records':len(records),'external_connections':197,
            'internal_bond_inspections':internal,'detailed_pdf_record_fields':'All 201 complete, exactly once',
            'reused_e2_diagram_pages':diagram_pages,'photo_files_reviewable':photos['count'],
            'actual_photo_terminal_matches':len(photos['actual_terminal_matches']),
            'checkpoint_count':10,'physical_measurements':'PENDING - no results invented',
            'firmware_changes':'NONE','physical_power_up':'HOLD retained','energized_stages':'F-J NOT RELEASED'}


if __name__=='__main__':
    result=check();(ROOT/'artifacts/team-handover-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
