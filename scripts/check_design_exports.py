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
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'electrical/design.json').read_text()); result=check(d)
nets={n['name']:n for n in d['nets']}; assigned={p:n['name'] for n in d['nets'] for p in n['nodes']}
with (ROOT/'electrical/connections.csv').open() as f:rows=list(csv.DictReader(f))
assert len(rows)==sum(len(n['nodes'])-1 for n in d['nets'])
assert len(set(r['wire_id'] for r in rows))==len(rows)
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
reader=PdfReader(ROOT/'docs/diagrams/electrical_package.pdf')
assert len(reader.pages)==manifest['pdf_pages']
assert all(len(p.extract_text())>100 for p in reader.pages),'Blank/unreadable PDF page'
text='\n'.join(p.extract_text() for p in PdfReader(ROOT/'docs/diagrams/complete_schematic.pdf').pages)
for ref in d['components']: assert re.search(r'\b'+re.escape(ref)+r'\s*\|',text),'Missing PDF component '+ref
for name in manifest['diagrams']:
    assert (ROOT/'docs/diagrams'/f'{name}.svg').is_file()
    assert len(PdfReader(ROOT/'docs/diagrams'/f'{name}.pdf').pages)==1
    ET.parse(ROOT/'docs/diagrams'/f'{name}.svg')
md=(ROOT/'docs/FINAL_WIRING.md').read_text()
assert all(r['wire_id'] in md for r in rows)
result.update({'wire_rows':len(rows),'all_svg_terminals':len(svgnodes),'pdf_pages':len(reader.pages),'export_check':'PASS; structural/readability only'})
print(json.dumps(result,indent=2))
