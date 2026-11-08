#!/usr/bin/env python3
"""Check generated connectivity, full SVG pin coverage and readable PDF contents.
Not electrical approval: actual modules/levels/ratings still require qualification.
"""
import csv,json,re
from collections import Counter,defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from pypdf import PdfReader
from check_electrical import check
from electrical_export_contracts import (
    check_pinout_svg, check_bts_overview_svg, check_internal_returns,
    check_classic_pdf_xref,
)
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'electrical/design.json').read_text()); result=check(d)
nets={n['name']:n for n in d['nets']}; assigned={p:n['name'] for n in d['nets'] for p in n['nodes']}
with (ROOT/'electrical/connections.csv').open() as f:rows=list(csv.DictReader(f))
assert len(rows)==sum(len(n['nodes'])-1 for n in d['nets'])
assert len(set(r['wire_id'] for r in rows))==len(rows)
check_internal_returns(rows)
expected_colors={'power_hc':'Red','power_lc':'Red','ground':'Black','control':'Blue','sensor':'Green','motor':'Orange'}
graph=defaultdict(lambda:defaultdict(set))
for r in rows:
    source=r['source'].split(' ')[0];dest=r['destination'].split(' ')[0]
    assert assigned[source]==assigned[dest]==r['net'],r
    assert r['status']==nets[r['net']]['status']
    assert r['color']==expected_colors[r['signal_type']]
    assert r['protection'] and r['verification'] and 'TBD' in r['conductor_class']
    graph[r['net']][source].add(dest);graph[r['net']][dest].add(source)
for name,n in nets.items():
    seen=set();todo=[n['nodes'][0]]
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p);todo.extend(graph[name][p]-seen)
    assert seen==set(n['nodes']),('Disconnected exported harness',name,set(n['nodes'])-seen)
with (ROOT/'electrical/terminal_map.csv').open() as f:terminals=list(csv.DictReader(f))
expected={ref+'.'+p for ref,c in d['components'].items() for p in c['pins']}
assert {r['component']+'.'+r['terminal'] for r in terminals}==expected
with (ROOT/'electrical/bom.csv').open() as f:bom=list(csv.DictReader(f))
assert {r['reference'] for r in bom}==set(d['components'])
svgnodes={}; counts=Counter()
for file in sorted((ROOT/'docs/diagrams').glob('complete_schematic_*.svg')):
    for e in ET.parse(file).iter():
        if 'data-terminal' in e.attrib:
            node=e.attrib['data-terminal'];counts[node]+=1;svgnodes[node]=e.attrib['data-net']
assert set(svgnodes)==expected and all(v==1 for v in counts.values()),'SVG terminal omissions/duplicates'
for node in expected: assert svgnodes[node]==assigned.get(node,'NO_CONNECT')
manifest=json.loads((ROOT/'electrical/export_manifest.json').read_text())
check_pinout_svg(ET.parse(ROOT/'docs/diagrams/esp32_pinout.svg').getroot(),d)
check_bts_overview_svg(ET.parse(ROOT/'docs/diagrams/motor_drivers.svg').getroot())
pdfs={}
for path in sorted((ROOT/'docs/diagrams').glob('*.pdf')):
    check_classic_pdf_xref(path.read_bytes())
    pdfs[path.name]=PdfReader(path,strict=True)
    assert all(len(p.extract_text())>100 for p in pdfs[path.name].pages), 'Blank/unreadable PDF page: '+path.name
reader=pdfs['electrical_package.pdf']
assert len(reader.pages)==manifest['pdf_pages']
text='\n'.join(p.extract_text() for p in pdfs['complete_schematic.pdf'].pages)
for ref in d['components']: assert re.search(r'\b'+re.escape(ref)+r'\s*\|',text),'Missing PDF component '+ref
for name in manifest['diagrams']:
    assert (ROOT/'docs/diagrams'/f'{name}.svg').is_file()
    assert len(pdfs[name+'.pdf'].pages)==1
    ET.parse(ROOT/'docs/diagrams'/f'{name}.svg')
# Critical visible labels must also reach the individual and combined PDFs.
package_text='\n'.join(p.extract_text() for p in reader.pages)
for filename,group_key in [('motor_drivers','data-driver'),('esp32_pinout','data-gpio')]:
    pdf_text=pdfs[filename+'.pdf'].pages[0].extract_text()
    root=ET.parse(ROOT/'docs/diagrams'/f'{filename}.svg').getroot()
    for group in (e for e in root.iter() if group_key in e.attrib):
        cursor=0
        for e in group:
            if not e.tag.endswith('text'):continue
            label=''.join(e.itertext())
            position=pdf_text.find(label,cursor)
            assert position>=0, 'SVG label missing/out of order in PDF: '+label
            cursor=position+len(label)
            assert label in package_text, 'Label missing from combined PDF: '+label
md=(ROOT/'docs/FINAL_WIRING.md').read_text()
assert all(r['wire_id'] in md for r in rows)
result.update({'wire_rows':len(rows),'all_svg_terminals':len(svgnodes),'pdf_pages':len(reader.pages),
               'strict_pdf_files':len(pdfs),'bts_return_labels':'PASS; no added return wires',
               'gpio_chart_statuses':'PASS; signal-route net status propagated',
               'export_check':'PASS; structural/semantic/PDF integrity only; physical release HOLD'})
print(json.dumps(result,indent=2))
