#!/usr/bin/env python3
"""Package existing E2 into a practical handover. Does not alter E2 or release hardware."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import html
import io
import json
import re

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, LongTable, Table, TableStyle,
    PageBreak, KeepTogether, Flowable,
)
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/team_handover'
WORK = ROOT / 'artifacts/team_handover_work'
PDF = ROOT / 'artifacts/TEAM_ASSEMBLY_HANDOVER.pdf'
PAGE = landscape(A3)
WIDTH = PAGE[0] - 80
AUTHORITIES = [
    'electrical/design.json', 'electrical/connections.csv', 'firmware/rover.ino',
    'include/rover_pins.h', 'docs/READY_TO_WIRE.md', 'docs/FINAL_PURCHASE_LIST.md',
    'docs/FINAL_GO_NO_GO.md', 'include/rover_control.h', 'platformio.ini',
    'wokwi/sketch.ino', 'wokwi/diagram.json',
]
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle('TeamTitle', fontName='Helvetica-Bold', fontSize=24, leading=29, spaceAfter=14, textColor=colors.HexColor('#12374b')))
STYLES.add(ParagraphStyle('TeamHeading', fontName='Helvetica-Bold', fontSize=13, leading=17, spaceBefore=10, spaceAfter=7, textColor=colors.HexColor('#12374b')))
STYLES.add(ParagraphStyle('TeamBody', fontName='Helvetica', fontSize=11, leading=15, spaceAfter=8))
STYLES.add(ParagraphStyle('TeamCell', fontName='Helvetica', fontSize=9, leading=12, spaceAfter=0, wordWrap='CJK'))
STYLES.add(ParagraphStyle('TeamSmall', fontName='Helvetica', fontSize=9, leading=12, spaceAfter=5))


def plain(value):
    return str(value).translate(str.maketrans({'→':'->', '—':'-', '–':'-', '≥':'>=', '≤':'<=', '×':'x', 'µ':'u', 'Ω':'ohm', '²':'2', '’':"'", '“':'"', '”':'"', '\u00a0':' '}))


def esc(value):
    return html.escape(plain(value))


def para(value, style='TeamBody', markdown=False):
    text=esc(value)
    if markdown:
        text=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#1565c0">\1</link>', text)
        text=re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        text=text.replace('`','')
    return Paragraph(text, STYLES[style])


def cell(value):
    return para(value, 'TeamCell', markdown=True)


def table(headers, rows, widths=None):
    data=[[cell(s) for s in headers]]+[[cell(s) for s in row] for row in rows]
    t=LongTable(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfeaf0')),
        ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#9babb6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7fa')]),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    return t


def make_pdf(path, story):
    doc=SimpleDocTemplate(str(path),pagesize=PAGE,leftMargin=40,rightMargin=40,topMargin=42,bottomMargin=32,
                          title='E2 team assembly handover',author='Rover project - E2 handover')
    def header(c,d):
        c.setFillColor(colors.HexColor('#526571'));c.setFont('Helvetica',8)
        c.drawString(40,PAGE[1]-25,'UNIVERSITY TEAM | E2 d6cd479 | unpowered progress allowed; energized stages NOT RELEASED')
    doc.build(story,onFirstPage=header,onLaterPages=header)


class TopDown(Flowable):
    """Proposed placement only; electrical identifiers come from E2."""
    def __init__(self):
        Flowable.__init__(self);self.width=WIDTH;self.height=500
    def draw(self):
        c=self.canv
        def box(x,y,w,h,title,desc,fill='#eef4f7'):
            c.setFillColor(colors.HexColor(fill));c.setStrokeColor(colors.HexColor('#335d72'))
            c.roundRect(x,y,w,h,8,fill=1,stroke=1)
            c.setFillColor(colors.HexColor('#12374b'));c.setFont('Helvetica-Bold',11);c.drawCentredString(x+w/2,y+h-20,title)
            c.setFont('Helvetica',9)
            for i,line in enumerate(desc):c.drawCentredString(x+w/2,y+h-37-i*13,line)
        c.setFillColor(colors.HexColor('#12374b'));c.setFont('Helvetica-Bold',16);c.drawCentredString(WIDTH/2,481,'FRONT / proposed cleaning and front-sensor end')
        box(160,25,WIDTH-320,430,'Proposed chassis envelope',['No scale; verify actual dimensions and clearances'], '#ffffff')
        box(420,390,260,55,'US_F',['Front sensor'])
        box(205,315,220,62,'M5 brush 1',['Inward sweep arrow to confirm'])
        box(WIDTH-425,315,220,62,'M6 brush 2',['Inward sweep arrow to confirm'])
        box(30,320,170,65,'M1 left-front',['DRV_L wheel pair'])
        box(30,100,170,65,'M2 left-rear',['DRV_L wheel pair'])
        box(WIDTH-200,320,170,65,'M3 right-front',['DRV_R wheel pair'])
        box(WIDTH-200,100,170,65,'M4 right-rear',['DRV_R wheel pair'])
        box(210,220,175,55,'US_L',['Left-facing bracket'])
        box(WIDTH-385,220,175,55,'US_R',['Right-facing bracket'])
        box(425,215,250,135,'M7 conveyor',['Travel toward collection bin','Mechanical route/guards TBD'], '#fff3df')
        c.setStrokeColor(colors.HexColor('#d87800'));c.setLineWidth(3)
        c.line(550,290,550,247);c.line(550,247,543,256);c.line(550,247,557,256)
        box(425,135,250,65,'Collection bin',['Actual volume and access TBD'])
        box(235,40,630,72,'Insulated electronics / protected power area',['ESP1, drivers, bucks, interface and reserved safety hardware','Keep power and signal harnesses separate; battery detached now'])
        c.setFont('Helvetica',9);c.drawString(210,10,'Sensor/brush/bin placements are proposals. Remote supervisor accepts actual layout from checkpoint A photos.')


def load_inputs():
    plan=json.loads((DATA/'plan.json').read_text())
    model=json.loads((ROOT/'electrical/design.json').read_text())
    with (ROOT/'electrical/connections.csv').open() as f: rows=list(csv.DictReader(f))
    return plan,model,rows


def photo_inventory():
    folder=ROOT/'docs/hardware_photos'
    extensions={'.jpg','.jpeg','.png','.heic','.webp','.tif','.tiff','.pdf'}
    images=sorted(str(p.relative_to(ROOT)) for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in extensions)
    return {'files':images,'count':len(images),'status':'NOT SUPPLIED' if not images else 'PRESENT - requires visual review',
            'visible_terminal_observations':[], 'actual_terminal_matches':[],
            'limit':'No actual marking, hidden terminal or rating is inferred by this generator.'}


def buy_now(model):
    items=[]
    for ref in ('U1','U2'):
        c=model['components'][ref];items.append({'item':c['value'],'quantity':1,'references':ref,'required':c['note']})
    groups={}
    for ref,c in model['components'].items():
        if c['kind']=='resistor' or (c['kind']=='capacitor' and c['value'].startswith('100nF')):
            groups.setdefault(c['value'],[]).append(ref)
    for value,refs in groups.items():
        items.append({'item':value+(' resistor' if refs[0].startswith('R') else ' ceramic capacitor'),
                      'quantity':len(refs),'references':', '.join(refs),
                      'required':'Fit actual package/mounting; effective capacitance at bias must meet E2.' if refs[0].startswith('C') else '1% tolerance, at least 1/8W, documented actual value/package.'})
    return items


def section_for(row):
    if row['connection_kind']=='INTERNAL_VERIFY':return 13
    a,b=[row[k].split()[0] for k in ('source','destination')]
    refs={a.split('.')[0],b.split('.')[0]}
    if any(p.startswith(('S2.','S3.','K1.','Z_COIL.','FK.')) or '.PG_' in p for p in (a,b)):return 11
    if 'ESP1' in refs:return 3
    for side,number,motors in [('DRV_L',4,{'M1','M2','FM1','FM2'}),('DRV_R',5,{'M3','M4','FM3','FM4'})]:
        if side in refs or refs&motors or refs&({'C_BL','Z_L'} if number==4 else {'C_BR','Z_R'}):return number
    if refs&{'DRV_A','M5','M6','M7','FM5','FM6','FM7','C_BA','Z_A'}:return 6
    if any(r.startswith('US_') for r in refs) or refs&{'R23','R24','R25','R26','R27','R28','C_F','C_L','C_R'}:return 7
    if refs&{'U1','U2','C_U1','C_U2'} or any(re.fullmatch(r'R\d+',r) for r in refs):return 8
    if refs&{'BUCK1','BUCK2','OV1','OV2','F1','F2'}:return 9
    return 10


def intermediate(row,model):
    if row['connection_kind']=='INTERNAL_VERIFY':
        return 'Existing internal module bond. NO WIRE TO ADD and no extra intermediate component. Inspect against the actual module schematic and unpowered reading.'
    refs={row[k].split('.')[0] for k in ('source','destination')}
    endpoint=[]
    for ref in sorted(refs):
        c=model['components'][ref]
        if c['kind'] in {'fuse','resistor','capacitor'} or ref.startswith(('OV','P1','K1','S2','S3')):
            endpoint.append(ref+' ['+c['name']+'; '+c['value']+']')
    s='No unnamed inline part in this segment.'
    if endpoint:s+=' Endpoint component(s): '+'; '.join(endpoint)+'.'
    # A segment ends at the named terminal; adjacent fuse/resistor/contact bodies
    # continue into other records and must never be installed a second time.
    s+=' Surrounding protection: '+row['protection']+'.'
    return s


def rating(row):
    if row['connection_kind']=='INTERNAL_VERIFY':
        return 'N/A: do not purchase or size another conductor for this existing bond. Verify the actual module and any shared-current path; do not infer its capacity from continuity.'
    refs={row[k].split('.')[0] for k in ('source','destination')}
    if row['conductor_class'].startswith('HIGH CURRENT') or row['signal_type'] in {'power_hc','motor'}:
        current='Current/AWG/mm2 NOT SELECTED: use actual run/start/stall, protective clearing, weakest pigtail/connector, route length/drop, ambient/bundling and thermal limits.'
    elif 'COIL' in row['net'] or refs&{'K1','S2','S3','FK','Z_COIL'}:
        current='Coil/contact or isolated control circuit: actual current, low-current wetting, contact isolation and coil range TBD per selected part. Never mix coil and GPIO contacts.'
    else:
        current='Signal/regulated branch only; actual load, leakage/pull network and conductor/connector suitability must be established. No numeric gauge/current invented.'
    return row['voltage']+'; '+row['conductor_class']+'. '+current+' Insulation/connector voltage must cover actual maximum normal and fault/transient exposure; expected voltage is not measured evidence.'


def connection_register(rows,model):
    result=[]
    for row in rows:
        result.append({**row,'handover_section':section_for(row),
            'action':'INSPECT EXISTING BOND - DO NOT ADD WIRE' if row['connection_kind']=='INTERNAL_VERIFY' else 'EXTERNAL CONNECTION - gate dependent',
            'intermediate_components':intermediate(row,model),'required_electrical_rating':rating(row),
            'team_verification_method':'UNPOWERED FIRST: isolate all sources and relevant loads; trace marked endpoints, record ohms/polarity and adjacent-net checks. E2 acceptance: '+row['verification']+'. Any scope/voltage/load test is FUTURE and stage-gated, not authorized by this row.'})
    return result


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def register_table(rows):
    entries=[]
    for r in rows:
        left='<b>Record '+esc(r['wire_id'])+'</b> | '+esc(r['action'])+'<br/>'
        left+='<b>Source:</b> '+esc(r['source'])+'<br/><b>Destination:</b> '+esc(r['destination'])+'<br/>'
        identification=(r['color']+' is the E2 reference color; '+r['net']+'; existing bond only, no new wire or end labels to fit.'
                        if r['connection_kind']=='INTERNAL_VERIFY' else r['color']+'; label both ends '+r['wire_id']+'; '+r['net'])
        left+='<b>Identification:</b> '+esc(identification)+'<br/>'
        left+='<b>Intermediate components:</b> '+esc(r['intermediate_components'])
        right='<b>Required electrical rating:</b> '+esc(r['required_electrical_rating'])+'<br/>'
        right+='<b>Verification:</b> '+esc(r['team_verification_method'])+'<br/>'
        right+='<b>E2 status retained:</b> '+esc(r['status'])+'; actual evidence PENDING.'
        entries.append([Paragraph(left,STYLES['TeamCell']),Paragraph(right,STYLES['TeamCell'])])
    t=LongTable([[cell('Connection / actual endpoints / intermediate protection'),cell('Required rating / verification / retained E2 dependency')]]+entries,
                 colWidths=[WIDTH*.49,WIDTH*.51],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#a5b4bd')),
                          ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfeaf0')),
                          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')]),
                          ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t


def checkpoint_story(plan):
    story=[]
    for i,cp in enumerate(plan['checkpoints']):
        if i:story.append(PageBreak())
        story += [para('Checkpoint '+cp['id']+' - '+cp['title'],'TeamTitle'),para(cp['state'],'TeamHeading'),
                  para('Prerequisites: '+cp['prerequisites'])]
        for n,instruction in enumerate(cp['instructions'],1):story.append(para(str(n)+'. '+instruction))
        story.append(table(['Evidence item','Required record'],[
            ['Photographs',cp['photos']],['Measurements',cp['measurements']],['PASS criteria',cp['pass']],
            ['STOP conditions',cp['stop']],['Send to remote supervisor',cp['send']],
            ['Actual result / acceptance','PENDING | assembler: ______ | reviewer: ______ | date: ______ | evidence batch: ______'],
        ],[165,WIDTH-165]))
    return story


def parse_purchase():
    text=(ROOT/'docs/FINAL_PURCHASE_LIST.md').read_text()
    lines=[line for line in text.splitlines() if line.startswith('|')]
    fields=[[v.strip() for v in line.strip('|').split('|')] for line in lines]
    return fields[0],fields[2:],text.split('## L298 decision and replacement path',1)[1]


def render_section(section,plan,model,records,photos,purchases):
    num=section['number'];story=[para(str(num)+'. '+section['title'],'TeamTitle')]
    story.append(para('Stage boundary: unpowered preparation permitted for identified items; physical power-up HOLD retained.','TeamSmall'))
    for text in section['instructions']:story.append(para(text))
    if num==1:
        story.append(para('Current photograph inventory: '+photos['status']+' ('+str(photos['count'])+' files).','TeamHeading'))
        groups=[('ESP1','ESP32 DevKit','GPIO/power/header and USB path; actual board unknown'),('DRV_L / DRV_R','Two BTS modules','All twelve functional ports per module; orientation/current unconfirmed'),('DRV_A','One conditional L298 carrier','Regulator/enable links, supply labels, diode paths and thermal capability unconfirmed'),('US_F/L/R','Three ultrasonic modules','Actual four-pin header labels unobserved'),('BUCK1/2','Two LM2596 modules','Input/output polarity/bonds and continuous capacity unconfirmed'),('M1-M7','Seven motors','Individual identities/lead labels and current profiles unconfirmed'),('BT1','Battery','User inventory: nominal 11.1V/3300mAh; actual label/chemistry unknown'),('P1, OV1/2, K1, S0/2/3','Required protection/stop assemblies','E2 functional names only; actual parts and terminal maps not selected'),('U1/U2 and passives','Fixed E2 interface selections','Selected part codes/values, not physically observed')]
        story.append(table(['E2 references','Inventory role','Actual identification status'],groups,[150,225,WIDTH-375]))
        story += [PageBreak(),para('Exact identification photographs needed','TeamTitle')]
        story.append(table(['Request / references','Requested filenames','Visible evidence and E2 comparison'],
            [[p['id']+' / '+p['references'],p['files'],p['needed']+' E2 match: '+p['e2_match']] for p in plan['photo_requests']],
            [130,315,WIDTH-445]))
        story.append(para('If images are later added, they require visual review and a recorded observation before any terminal can be marked matched. Photo filenames alone do not close a gate.','TeamSmall'))
    if num==2:story.extend([Spacer(1,10),TopDown()])
    if num==3:
        gpio=model['gpio_bindings']
        story.append(table(['Firmware signal','GPIO','E2 endpoint / net'],[[name,str(b['gpio']),b['endpoint']+' / '+b['net']] for name,b in gpio.items()],[200,70,WIDTH-270]))
    if num==12:
        story.append(para('Purchase now: fixed E2 selections','TeamHeading'))
        story.append(table(['Component','Qty','Reference labels','Mounting / specification note'],
            [[r['item'],str(r['quantity']),r['references'],r['required']] for r in purchases],[230,45,365,WIDTH-640]))
        story.append(para('This is 2 ICs, 32 resistors and 5 capacitors; adapter purchase requires verified package-to-header mapping. Motor/power hardware remains conditional.'))
        story += [PageBreak(),para('Complete E2 conditional purchase specification','TeamTitle')]
        headers,rows,tail=parse_purchase()
        story.append(table(headers,rows,[195,42,255,210,48,WIDTH-750]))
        story += [PageBreak(),para('L298 conditional replacement and required design revision','TeamTitle')]
        for p in tail.split('\n\n'):
            p=p.strip()
            if not p or p.startswith('## Source verification'):continue
            story.append(para(p,markdown=True))
        story += [PageBreak(),para('Missing measurements: collect data now; powered entries stay gated','TeamTitle')]
        story.append(table(['ID / when','Item','Exact data needed','Acceptance / selection dependency'],
            [[m['id']+' / '+m['stage'],m['item'],m['required'],m['acceptance']] for m in plan['measurements']],
            [160,140,410,WIDTH-710]))
    if num==13:
        story.append(table(['Checkpoint','Current permission','Result'],[[cp['id']+' - '+cp['title'],cp['state'],'PENDING / not executed'] for cp in plan['checkpoints']],[300,WIDTH-460,160]))
        story += [PageBreak()]+checkpoint_story(plan)
    narrative=WORK/f'section_{num:02}_narrative.pdf';make_pdf(narrative,story)
    pieces=[narrative]+[ROOT/'docs/diagrams'/f'{name}.pdf' for name in section['diagrams']]
    selected=[r for r in records if r['handover_section']==num]
    if selected:
        heading=('Four internal-bond verification records - NO ADDITIONAL WIRES' if num==13 else 'Detailed connection records - '+section['title'])
        s=[para(heading,'TeamTitle'),para('A record is one E2 segment. Endpoint resistor/fuse/contact bodies continue into other records; do not install duplicate components or jumpers. Color identifies function; voltage and ratings are requirements, not measurements.','TeamSmall'),register_table(selected)]
        path=WORK/f'section_{num:02}_connections.pdf';make_pdf(path,s);pieces.append(path)
    return pieces


def write_team_files(plan,model,records,photos,purchases):
    write_csv(DATA/'TEAM_CONNECTION_REGISTER.csv',records)
    template=[]
    for r in records:
        template.append({k:r[k] for k in ('wire_id','action','source','destination','net','color','handover_section')} | {
            'actual_source_terminal':'','actual_destination_terminal':'','approved_conductor_or_existing_bond':'',
            'status':'PENDING','test_lead_ohms':'','measured_value':'','unit':'','approved_limit':'',
            'instrument_method':'','evidence_files':'','assembler':'','reviewer':'','date':'','deviation_or_reason_pending':''})
    write_csv(DATA/'TEAM_ASSEMBLY_RECORD.csv',template)
    checkpoint_rows=[]
    for cp in plan['checkpoints']:
        phases=['MOTOR-FREE PREFLIGHT - required before H','LOADED CONFIRMATION - after H'] if cp['id']=='I' else ['']
        for phase in phases:
            checkpoint_rows.append({'checkpoint':cp['id'],'title':cp['title'],'current_permission':cp['state'],
                'result':'PENDING','motor_free_or_loaded_I':phase,'evidence_batch':'','accepted_scope':'','reviewer':'','date':'','outstanding_items':''})
    write_csv(DATA/'TEAM_CHECKPOINT_RECORD.csv',checkpoint_rows)
    write_csv(DATA/'TEAM_MEASUREMENT_RECORD.csv',[{'measurement_id':m['id'],'item':m['item'],'when':m['stage'],'required':m['required'],
              'acceptance':m['acceptance'],'actual_value_unit':'','part_or_wire_ids':'','conditions_instrument':'','manufacturer_or_trace_file':'','result':'PENDING','reviewer_date':''} for m in plan['measurements']])
    write_csv(DATA/'TEAM_TERMINAL_MAP.csv',[{'reference':ref,'e2_functional_pin':pin,'function':function,
              'actual_part_revision':'','actual_printed_terminal':'','photo_file':'','datasheet_page':'','unpowered_mapping_method':'','result':'PENDING'}
              for ref,c in model['components'].items() if c['kind'] not in {'resistor','capacitor','fuse','motor'} for pin,function in c['pins'].items()])
    write_csv(DATA/'PURCHASE_NOW.csv',purchases)
    (DATA/'photo_inventory.json').write_text(json.dumps(photos,indent=2)+'\n')
    text='# Hardware photograph request - E2 team handover\n\nNo photographs were supplied when this handover was prepared. This folder was created for team evidence. No actual terminal label, component marking or rating has been visually verified. Add original-resolution images using these names (PNG is also acceptable); do not expose/open the battery or probe its connectors for identification.\n\n'
    for p in plan['photo_requests']:
        text+='## '+p['id']+' - '+p['references']+'\n\nFiles: '+p['files']+'\n\n'+p['needed']+'\n\nE2 comparison: '+p['e2_match']+'\n\n'
    text+='Fill `docs/team_handover/TEAM_TERMINAL_MAP.csv` from visible labels and actual manufacturer documentation. Missing or unreadable values stay PENDING. Photographs require review; filenames alone are not evidence of compatibility.\n'
    (ROOT/'docs/hardware_photos/README.md').write_text(text)
    text='# Team assembly handover - E2 baseline d6cd479\n\n[Open the team PDF](../artifacts/TEAM_ASSEMBLY_HANDOVER.pdf). This is a focused assembly handover, not a new master review. E2 sources, GPIOs and firmware are unchanged. Physical power-up HOLD remains; checkpoint A and identified unpowered portions of B/C/D can proceed.\n\n'
    text+='## Start here\n\nKeep battery main/balance, USB and every source disconnected; motor ends isolated. Start checkpoint A: mark FRONT, label every module/motor, dry-fit mounts and guards, measure routing with string, and send top/underside/ruler photographs. Keep battery detached. Do not terminate unknown-rated power branches.\n\n'
    text+='No hardware photographs were supplied. Exact images needed: [photo request](hardware_photos/README.md). Actual terminal matches remain unverified.\n\n'
    text+='## Purchase now\n\n| Item | Qty | References |\n|---|---:|---|\n'
    for r in purchases:text+='| '+r['item']+' | '+str(r['quantity'])+' | '+r['references']+' |\n'
    text+='\nObtain a carrier matching U2 DCU VSSOP8 only after checking its mechanical/pad/header map. Power/current-dependent hardware is conditional; use [E2 purchase specification](FINAL_PURCHASE_LIST.md).\n\n'
    text+='## Connection records\n\nThe PDF uses all 201 E2 records: 197 external segments, plus W042/W044/W046/W048 as existing internal-bond inspections, never added wires. The generated [connection register](team_handover/TEAM_CONNECTION_REGISTER.csv) retains canonical source, destination, color, net/status and protection, adding intermediate-component explanation, rating criteria and stage-aware verification.\n\n'
    text+='Use blank evidence templates: [wire readings](team_handover/TEAM_ASSEMBLY_RECORD.csv), [terminal mapping](team_handover/TEAM_TERMINAL_MAP.csv), [measurements](team_handover/TEAM_MEASUREMENT_RECORD.csv), [checkpoint record](team_handover/TEAM_CHECKPOINT_RECORD.csv). Preserve originals; copy templates to dated team evidence batches rather than overwriting generated masters.\n\n'
    text+='## What stays disconnected\n\nBattery main and balance, all actual motor loads/high-current branches, unselected P1/OV1/OV2/K1/contact ports, external buck/MCU power and real ECHO-to-MCU plugs. Do not bypass missing protection, hard-enable drivers, parallel buck positives, connect a motor output to ground, or add four internal-bond jumpers. Identified detached signal/protection assemblies may be prepared unpowered; full harness termination waits for its actual pin/rating evidence.\n\n'
    text+='## Checkpoints and remote evidence\n\nOrder: A -> applicable B -> C plus D -> E -> F -> G -> I motor-free preflight -> H -> I loaded confirmation -> J. All energized F-J stages are NOT RELEASED. Each checkpoint in the PDF gives instructions, photographs, measurements, PASS and STOP criteria.\n\n'
    for cp in plan['checkpoints']:
        text+='### '+cp['id']+' - '+cp['title']+'\n\n'+cp['state']+'\n\nSend: '+cp['send']+'\n\n'
    text+='## Exact missing measurements\n\n'
    for m in plan['measurements']:text+='- **'+m['id']+' / '+m['item']+'** ('+m['stage']+'): '+m['required']+' Acceptance: '+m['acceptance']+'\n'
    text+='\n## Rebuild and validate\n\n```sh\n.venv/bin/python scripts/generate_team_handover.py\n.venv/bin/python scripts/check_team_handover.py\n```\n\nThe PDF reuses E2 vector PDF pages without changing them, includes a proposed top-down placement and all 13 requested sections, and carries bookmarks/page numbers. Generator inputs and included diagrams are fingerprinted in `docs/team_handover/manifest.json`. No virtual check establishes physical compatibility.\n'
    (ROOT/'docs/TEAM_HANDOVER.md').write_text(text)


def main():
    WORK.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    plan,model,rows=load_inputs();photos=photo_inventory();purchases=buy_now(model)
    records=connection_register(rows,model);write_team_files(plan,model,records,photos,purchases)
    section_pieces={s['number']:render_section(s,plan,model,records,photos,purchases) for s in plan['sections']}
    lengths={n:sum(len(PdfReader(p,strict=True).pages) for p in paths) for n,paths in section_pieces.items()}
    starts={};cursor=2
    for s in plan['sections']:starts[s['number']]=cursor;cursor+=lengths[s['number']]
    cover=[para('TEAM ASSEMBLY HANDOVER','TeamTitle'),para('Autonomous garbage collection rover | E2 baseline d6cd479 | 8 November 2026','TeamHeading'),
           para('START NOW: checkpoint A - disconnected mounting, reference labels, proposed layout and route measurements. Protected detached signal assembly follows verified component/package mapping.'),
           para('KEEP DISCONNECTED: battery main/balance, every supply/USB during assembly, actual motor loads, unresolved protection/power ports and actual ECHO-to-MCU plugs. F-J energized stages are NOT RELEASED.'),
           para('201 E2 records = 197 external segments + 4 internal-bond inspections (NO added wires). E2 baseline has 119 passing software tests; these do not establish actual compatibility. No supplied hardware photographs; no actual terminal matches yet.'),
           table(['Section','Page'],[[str(s['number'])+'. '+s['title'],str(starts[s['number']])] for s in plan['sections']],[WIDTH-80,80]),
           Spacer(1,10),para('Remote review: send labeled top/underside and terminal photographs, exact-part documents, completed wire/terminal/measurement records and a checkpoint evidence batch. PENDING is never PASS.','TeamSmall')]
    cover_path=WORK/'cover.pdf';make_pdf(cover_path,cover);assert len(PdfReader(cover_path).pages)==1
    writer=PdfWriter();writer.append(str(cover_path),import_outline=False)
    included=[];sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in AUTHORITIES+[
        'docs/team_handover/plan.json', 'scripts/generate_team_handover.py']}
    page_roles=[{'page':1,'role':'cover','source':'generated'}]
    for s in plan['sections']:
        parent=writer.add_outline_item(str(s['number'])+'. '+s['title'],starts[s['number']]-1)
        for path in section_pieces[s['number']]:
            start=len(writer.pages)+1;reader=PdfReader(path,strict=True)
            writer.append(reader,import_outline=False)
            relative=str(path.relative_to(ROOT))
            for i in range(len(reader.pages)):page_roles.append({'page':start+i,'section':s['number'],'role':'E2 diagram' if path.parent==ROOT/'docs/diagrams' else 'generated','source':relative,'source_page':i+1})
            if path.parent==ROOT/'docs/diagrams':
                included.append(relative);sources[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
                writer.add_outline_item(path.stem,start-1,parent=parent)
    total=len(writer.pages)
    for i,page in enumerate(writer.pages):
        buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(float(page.mediabox.width),float(page.mediabox.height)))
        c.setFillColor(colors.HexColor('#526571'));c.setFont('Helvetica',8)
        c.drawRightString(float(page.mediabox.width)-22,float(page.mediabox.height)-13,f'Team handover | page {i+1} / {total}')
        c.save();buf.seek(0);page.merge_page(PdfReader(buf).pages[0])
    writer.add_metadata({'/Title':'TEAM ASSEMBLY HANDOVER - E2 d6cd479','/Author':'Autonomous rover university team','/Subject':'197 external connection segments + 4 internal inspections; unpowered work and evidence-gated commissioning'})
    for name in ('TEAM_ASSEMBLY_RECORD.csv','TEAM_CHECKPOINT_RECORD.csv'):
        writer.add_attachment(name,(DATA/name).read_bytes())
    with PDF.open('wb') as f:writer.write(f)
    reader=PdfReader(PDF,strict=True);record_pages={}
    for i,page in enumerate(reader.pages):
        for wire in re.findall(r'Record\s+(W\d{3})\b',page.extract_text()):
            assert wire not in record_pages, 'Duplicate detailed connection '+wire
            record_pages[wire]=i+1
    assert set(record_pages)=={r['wire_id'] for r in records}
    for r in records:r['pdf_page']=record_pages[r['wire_id']]
    write_csv(DATA/'TEAM_CONNECTION_REGISTER.csv',records)
    manifest={'baseline_commit':plan['baseline_commit'],'handover_date':plan['date'],'scope':plan['scope'],
              'pdf':str(PDF.relative_to(ROOT)),'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pdf_pages':total,
              'section_starts':starts,'section_lengths':lengths,'page_roles':page_roles,'included_e2_diagrams':included,
              'source_sha256':sources,'connection_records':len(records),'external_connections':sum(r['connection_kind']=='WIRE' for r in records),
              'internal_bond_ids':[r['wire_id'] for r in records if r['connection_kind']=='INTERNAL_VERIFY'],
              'photo_inventory':photos,'purchase_now':purchases,'all_physical_checkpoint_results':'PENDING / NOT EXECUTED',
              'physical_power_up':'HOLD retained','firmware_changes':'NONE'}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'pdf':str(PDF.relative_to(ROOT)),'pages':total,'sections':13,'records':len(records),'external_wires':197,'internal_inspections':4,'hardware_photos':photos['count'],'physical_power_up':'HOLD'},indent=2))


if __name__=='__main__':main()
