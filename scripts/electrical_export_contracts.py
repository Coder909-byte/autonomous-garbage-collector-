"""Semantic guards for E1 drawings and classic-xref PDF exports; no hardware I/O."""
import re


def gpio_route_status(model, name):
    """Use the most restrictive status on the signal nets shown in this row."""
    nets = {net['name']: net for net in model['nets']}
    assigned = {node: net['name'] for net in model['nets'] for node in net['nodes']}
    binding = model['gpio_bindings'][name]
    route = {binding['net']}
    if 'buffer_out' in binding:
        route.add(assigned['U1.' + binding['buffer_out']])
    if name == 'ENABLE':
        route.add('EN_DRIVER_5V')
    if name in ('EF', 'EL', 'ER'):
        route.update((name + '_RAW', name + '_DIV', 'V3V3'))
    if name == 'ESTOP_OK':
        route.update(('V3V3', 'SENSE_STOP_OK'))
    priority = {'PROVISIONAL': 0, 'BLOCKED_RATING': 1, 'BLOCKED_MISSING': 2}
    return max((nets[n]['status'] for n in route), key=priority.__getitem__)


def check_pinout_svg(root, model):
    groups = [e for e in root.iter() if 'data-gpio' in e.attrib]
    assert len(groups) == len(model['gpio_bindings']), 'Missing/duplicate GPIO chart row'
    seen = set()
    for group in groups:
        name = group.attrib['data-signal']
        assert name not in seen, 'Duplicate GPIO signal row'
        seen.add(name)
        binding = model['gpio_bindings'][name]
        assert int(group.attrib['data-gpio']) == binding['gpio'], 'Chart GPIO mismatch'
        labels = [''.join(e.itertext()) for e in group if e.tag.endswith('text')]
        assert 'GPIO' + str(binding['gpio']) in labels, 'Missing visible GPIO label'
        statuses = [e for e in group if e.attrib.get('data-role') == 'route-status']
        assert len(statuses) == 1, 'Missing/duplicate visible electrical status'
        assert ''.join(statuses[0].itertext()) == gpio_route_status(model, name), 'Understated/mismatched route status: ' + name
        notes = [e for e in group if e.attrib.get('data-role') == 'route-note']
        assert len(notes) == 1 and ''.join(notes[0].itertext()).strip(), 'Missing qualification note'
    assert seen == set(model['gpio_bindings']), 'Missing GPIO signals'


def check_bts_overview_svg(root):
    groups = {e.attrib['data-driver']: e for e in root.iter() if 'data-driver' in e.attrib}
    for ref in ('DRV_L', 'DRV_R'):
        assert ref in groups, 'Missing BTS overview card: ' + ref
        labels = [''.join(e.itertext()) for e in groups[ref] if e.tag.endswith('text')]
        text = '\n'.join(labels)
        assert re.search(r'B-\s*->\s*TB_GND.*branch-rated', text), 'Missing dedicated B- power return: ' + ref
        assert 'GND/B- internal bond: VERIFY; no extra return wire' in labels, 'Missing internal-bond/no-extra-wire qualification: ' + ref
        assert 'GND -> power return' not in text, 'Ambiguous logic-header return: ' + ref


def check_internal_returns(rows):
    """Existing module bonds are verification tasks, never new return jumpers."""
    expected = {
        ('BUCK1.IN-', 'BUCK1.OUT-'), ('BUCK2.IN-', 'BUCK2.OUT-'),
        ('DRV_L.B-', 'DRV_L.GND'), ('DRV_R.B-', 'DRV_R.GND'),
    }
    actual = {(r['source'].split(' ')[0], r['destination'].split(' ')[0])
              for r in rows if r['connection_kind'] == 'INTERNAL_VERIFY'}
    assert actual == expected, 'Internal bonds must remain INTERNAL_VERIFY'
    for ref in ('DRV_L', 'DRV_R'):
        supply_return = [r for r in rows if r['destination'] == ref + '.B-']
        assert len(supply_return) == 1
        row = supply_return[0]
        assert row['source'] == 'TB_GND.BUS' and row['connection_kind'] == 'WIRE'
        assert row['conductor_class'].startswith('HIGH CURRENT'), 'Power return not branch-rated'
        assert not any(r['destination'] == ref + '.GND' and r['connection_kind'] == 'WIRE' for r in rows), 'Unintended extra logic-ground return'


def check_classic_pdf_xref(data):
    """Validate offsets in our generated single-revision, classic-xref PDFs.

    This is an additional byte-level guard, not a general PDF parser. Export
    validation also uses pypdf strict mode and extracts every page's contents.
    """
    assert data.startswith(b'%PDF-'), 'Invalid PDF header'
    match = re.search(rb'startxref\s+(\d+)\s+%%EOF\s*$', data)
    assert match, 'Missing final PDF startxref/EOF'
    offset = int(match[1])
    assert data[offset:offset + 4] == b'xref', 'Broken PDF startxref offset'
    section = data[offset:].split(b'trailer', 1)
    assert len(section) == 2, 'Missing PDF trailer'
    lines = section[0].splitlines()[1:]
    cursor = 0
    while cursor < len(lines):
        if not lines[cursor].strip():
            cursor += 1
            continue
        header = re.fullmatch(rb'(\d+)\s+(\d+)', lines[cursor].strip())
        assert header, 'Invalid xref subsection'
        first, count = map(int, header.groups())
        cursor += 1
        assert cursor + count <= len(lines), 'Truncated xref table'
        for number, line in enumerate(lines[cursor:cursor + count], first):
            entry = re.fullmatch(rb'(\d{10})\s+(\d{5})\s+([nf])\s*', line)
            assert entry, 'Invalid xref entry'
            if entry[3] == b'n':
                object_offset, generation = int(entry[1]), int(entry[2])
                prefix = f'{number} {generation} obj'.encode()
                assert data[object_offset:object_offset + len(prefix)] == prefix, 'Broken PDF object offset'
        cursor += count
