#!/usr/bin/env python3
"""Cross-check E2 assembly sheets and instructions against exported connection data."""
from pathlib import Path
import csv, json, sys
import xml.etree.ElementTree as ET
from generate_ready_to_wire import generate

ROOT=Path(__file__).resolve().parents[1]

def check():
    with (ROOT/'electrical/connections.csv').open() as f: rows=list(csv.DictReader(f))
    expected={r['wire_id']:(r['source'].split()[0],r['destination'].split()[0]) for r in rows}
    seen={}
    for path in sorted((ROOT/'docs/diagrams').glob('assembly_connections_*.svg')):
        for g in ET.parse(path).iter():
            if 'data-wire-id' not in g.attrib: continue
            key=g.attrib['data-wire-id']
            assert key not in seen, 'Duplicate simplified wire '+key
            seen[key]=(g.attrib['data-source'],g.attrib['data-destination'])
            labels=[''.join(e.itertext()) for e in g if e.tag.endswith('text')]
            r=next(r for r in rows if r['wire_id']==key)
            assert r['source']+' -> '+r['destination'] in labels, 'Invisible endpoint mismatch '+key
    assert seen==expected, 'Simplified sheets differ from canonical connection table'
    assert (ROOT/'docs/READY_TO_WIRE.md').read_text()==generate(rows), 'Assembly instructions drifted'
    model=json.loads((ROOT/'electrical/design.json').read_text())
    assigned={p:n['name'] for n in model['nets'] for p in n['nodes']}
    # Reconstruct graph from exported wires separately from model checker.
    adj={}
    for a,b in seen.values():
        assert assigned[a]==assigned[b], ('Cross-net wire',a,b)
        adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
    for n in model['nets']:
        reached=set();pending=[n['nodes'][0]]
        while pending:
            node=pending.pop()
            if node in reached:continue
            reached.add(node);pending.extend(adj.get(node,set())-reached)
        assert reached==set(n['nodes']), 'Disconnected wire net '+n['name']
    return {'simplified_connections':len(seen),'assembly_steps':len(rows),'independent_graph_nets':len(model['nets']),
            'result':'PASS - file consistency only; electrical/physical release HOLD'}

if __name__=='__main__': print(json.dumps(check(),indent=2))
