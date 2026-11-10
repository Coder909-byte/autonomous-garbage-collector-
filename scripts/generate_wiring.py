#!/usr/bin/env python3
"""Generate E2 diagrams/tables from design.json. Does not generate PCB footprints."""
from pathlib import Path
import csv,html,json,math,textwrap
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from pypdf import PdfReader,PdfWriter
from PIL import Image,ImageDraw,ImageFont
from check_electrical import check
from electrical_export_contracts import gpio_route_status, check_classic_pdf_xref
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/diagrams'
D=json.loads((ROOT/'electrical/design.json').read_text()); check(D)
C=D['components']; N={n['name']:n for n in D['nets']}
PIN_NET={p:n for n in D['nets'] for p in n['nodes']}
COL={'power_hc':'#c62828','power_lc':'#c62828','ground':'#17232c','control':'#1565c0','sensor':'#23844b','motor':'#d87800'}
W,H=1680,1188
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def write_validated_pdf(writer,path):
    candidate=path.with_name('.'+path.name+'.tmp')
    try:
        with candidate.open('wb') as f:writer.write(f)
        check_classic_pdf_xref(candidate.read_bytes())
        reader=PdfReader(candidate,strict=True)
        assert all(p.extract_text().strip() for p in reader.pages), 'Blank PDF candidate page'
        candidate.replace(path)
    finally:
        candidate.unlink(missing_ok=True)
def label(node):
    ref,pin=node.split('.',1); name=C[ref]['pins'][pin]
    return ref+'.'+pin+(' ('+name+')' if name!=pin else '')
def txt(s): return str(s).replace('Ω','ohm').replace('→','->').replace('≤','<=').replace('≥','>=').replace('—','-').replace('–','-')
class Drawing:
    def __init__(self,title,subtitle,revision="E2",date="08 Nov 2026"):
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 {W} {H}">',f'<title>{html.escape(title)}</title>','<rect width="1680" height="1188" fill="white"/>']
        self.pdf=canvas.Canvas(str(OUT/'_current.pdf'),pagesize=landscape(A3));self.pdf.scale(landscape(A3)[0]/W,landscape(A3)[1]/H)
        self.pdf.setTitle(title+' - '+revision+' PROVISIONAL')
        self.image=Image.new('RGB',(W,H),'white');self.im=ImageDraw.Draw(self.image)
        self.text(42,46,title,27,bold=True);self.text(42,76,subtitle,15)
        self.rect(42,90,1596,34,fill='#fff2d8',stroke='#ad6a00')
        self.text(53,113,revision+' DESIGN HOLD | Physical connections unapproved | Generic ports require actual-part mapping | '+date,16,bold=True)
        self.text(42,1141,'Red +supply | Black GND | Blue control | Green sensor | Orange motor | Thick = high-current | Dashed = missing/blocked',14)
        self.text(42,1166,'Net labels join across sheets. Crossings alone do not join. No component footprint / connector orientation is implied.',14)
    def rect(self,x,y,w,h,fill='white',stroke='#576572',dash=False):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"'+(' stroke-dasharray="7 4"' if dash else '')+'/>')
        self.pdf.setFillColor(colors.toColor(fill));self.pdf.setStrokeColor(colors.HexColor(stroke));self.pdf.setDash(5,3) if dash else self.pdf.setDash();self.pdf.rect(x,H-y-h,w,h,fill=1,stroke=1);self.pdf.setDash()
        self.im.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=2)
    def line(self,points,color='#1565c0',width=2,dash=False):
        self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="8 5"' if dash else '')+'/>')
        self.pdf.setStrokeColor(colors.HexColor(color));self.pdf.setLineWidth(width);self.pdf.setDash(7,4) if dash else self.pdf.setDash()
        p=self.pdf.beginPath();p.moveTo(points[0][0],H-points[0][1])
        for x,y in points[1:]:p.lineTo(x,H-y)
        self.pdf.drawPath(p);self.pdf.setDash()
        self.im.line(points,fill=color,width=max(1,int(width)))
    def text(self,x,y,s,size=14,color='#17232c',bold=False):
        s=txt(s)
        assert 0<=x<W and 0<y<H,(s,x,y)
        assert x+stringWidth(s,'Helvetica-Bold' if bold else 'Helvetica',size)<W-20,('Text exceeds page',s,x,size)
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" font-weight="'+('bold' if bold else 'normal')+f'" fill="{color}">{html.escape(s)}</text>')
        self.pdf.setFont('Helvetica-Bold' if bold else 'Helvetica',size);self.pdf.setFillColor(colors.HexColor(color));self.pdf.drawString(x,H-y,s)
        font=ImageFont.truetype(BOLD if bold else FONT,int(size)) if Path(FONT).exists() else ImageFont.load_default(size=int(size))
        self.im.text((x,y-size*.81),s,font=font,fill=color)
    def lines(self,x,y,s,width=75,size=14,leading=20,color='#17232c',bold=False):
        for i,line in enumerate(textwrap.wrap(txt(s),width=width,break_long_words=False)):
            self.text(x,y+i*leading,line,size,color,bold)
    def dot(self,x,y,color='#17232c'):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        self.pdf.setFillColor(colors.HexColor(color));self.pdf.circle(x,H-y,4,fill=1,stroke=0);self.im.ellipse((x-4,y-4,x+4,y+4),fill=color)
    def card(self,x,y,w,h,title,lines,missing=False):
        self.rect(x,y,w,h,fill='#fff9ed' if missing else '#f4f7fb',dash=missing)
        self.text(x+12,y+25,title,17,bold=True)
        for i,line in enumerate(lines): self.text(x+12,y+49+i*21,line,14)
    def save(self,name):
        (OUT/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>'])+'\n')
        self.pdf.save();(OUT/'_current.pdf').replace(OUT/(name+'.pdf'))
        self.image.save(OUT/(name+'.png'))

def component_height(ref): return 87+20*len(C[ref]['pins'])
def component(d,ref,x,y,w=500):
    c=C[ref]; h=component_height(ref)
    d.rect(x,y,w,h,fill='#f7f9fc' if c['in_inventory'] else '#fffaf0',dash=not c['in_inventory'])
    title=ref+' | '+c['name']
    if stringWidth(title,'Helvetica-Bold',16)>w-20:
        title=ref+' | '+c['kind'].upper()+' - see BOM'
    d.text(x+10,y+24,title,16,bold=True)
    d.text(x+10,y+45,'INVENTORY / VERIFY' if c['in_inventory'] else 'ADDITIONAL / MISSING OR SELECT',13,color='#995b00')
    value=c['value'] or c['kind']+' terminal symbol'
    if len(value)>58:value=value[:55]+'...'
    d.text(x+10,y+65,value,13)
    for i,(pin,function) in enumerate(c['pins'].items()):
        yy=y+89+i*20; node=ref+'.'+pin; net=PIN_NET.get(node)
        text=pin if pin==function else pin+' / '+function
        d.text(x+12,yy,text,13)
        if net:
            col=COL[net['kind']];width=5 if net['kind']=='power_hc' or (net['kind']=='ground' and ref in ('BT1','DRV_L','DRV_R','DRV_A','TB_GND','C_BL','C_BR','C_BA','Z_L','Z_R','Z_A')) else 2
            d.line([(x+208,yy-5),(x+248,yy-5)],col,width,net['status'].startswith('BLOCKED'))
            d.text(x+258,yy,net['name'],13,col)
            d.svg[-1]=d.svg[-1].replace('<text ',f'<text data-terminal="{node}" data-net="{net["name"]}" ',1)
        else:
            d.text(x+258,yy,'NC - INSULATE',13,color='#995b00')
            d.svg[-1]=d.svg[-1].replace('<text ',f'<text data-terminal="{node}" data-net="NO_CONNECT" ',1)
    if len(c['pins'])==2 and c['kind'] in ('resistor','capacitor','fuse','motor'):
        yy=y+84
        if c['kind']=='resistor': d.line([(x+208,yy),(x+204,yy+3),(x+212,yy+6),(x+204,yy+10),(x+212,yy+14),(x+208,yy+20)],'#576572',1.5)
        elif c['kind']=='capacitor':
            d.line([(x+208,yy),(x+208,yy+7)],'#576572');d.line([(x+199,yy+7),(x+217,yy+7)],'#576572')
            d.line([(x+199,yy+12),(x+217,yy+12)],'#576572');d.line([(x+208,yy+12),(x+208,yy+20)],'#576572')
        elif c['kind']=='fuse': d.rect(x+204,yy+3,8,14,fill='white')
        else: d.text(x+193,yy+17,'M',13,bold=True)
    return h

def schematics():
    order=['BT1','F0','S0','P1','TB_POS','TB_GND','K1','S2','S3','OV1','OV2','Z_COIL','Z_L','Z_R','Z_A','F1','BUCK1','F2','BUCK2','FK','FL','FR','FA','ESP1','U1','DRV_L','DRV_R','DRV_A','US_F','US_L','US_R']
    order += [r for r in C if r not in order]
    pages=[];page=0;d=None;ys=[]
    for ref in order:
        h=component_height(ref)
        if d is None or min(ys)+h>1102:
            if d: d.save('complete_schematic_'+str(page).zfill(2));pages.append('complete_schematic_'+str(page).zfill(2))
            page+=1;d=Drawing(f'Complete schematic - sheet {page}','Every component terminal is shown. Equal net labels are connected; use connection IDs in the CSV for physical routing.');ys=[148]*3
        col=min(range(3),key=lambda k:ys[k]); component(d,ref,42+col*534,ys[col]);ys[col]+=h+16
    if d:d.save('complete_schematic_'+str(page).zfill(2));pages.append('complete_schematic_'+str(page).zfill(2))
    writer=PdfWriter()
    for name in pages:writer.append(OUT/(name+'.pdf'))
    write_validated_pdf(writer,OUT/'complete_schematic.pdf')
    return pages

def pinout():
    d=Drawing('ESP32 pinout connection chart','Functional GPIO labels only. Exact DevKit header positions/USB power path remain unverified; no wiring orientation implied.')
    destinations={'L_FWD':'U1.2 -> U1.18 -> DRV_L.RPWM','L_REV':'U1.4 -> U1.16 -> DRV_L.LPWM','R_FWD':'U1.6 -> U1.14 -> DRV_R.RPWM','R_REV':'U1.8 -> U1.12 -> DRV_R.LPWM','ENABLE':'U1.11 -> U1.9 -> S2 EN NC -> six enables','TF':'U1.13 -> U1.7 -> US_F.TRIG','TL':'U1.15 -> U1.5 -> US_L.TRIG','TR':'U1.17 -> U1.3 -> US_R.TRIG','BRUSH_IN1':'DRV_A.IN1 / both brushes','BRUSH_IN2':'DRV_A.IN2 / held LOW','CONVEYOR_IN3':'DRV_A.IN3 / conveyor','CONVEYOR_IN4':'DRV_A.IN4 / held LOW','EF':'ECHO -> R23/R24 -> U2.1/7 -> GPIO34','EL':'ECHO -> R25/R26 -> U2.3/5 -> GPIO35','ER':'ECHO -> R27/R28 -> U2.6/2 -> GPIO36 / VP','ESTOP_OK':'3V3 -> S2 NC -> K1 sense NO -> GPIO27'}
    notes={'ENABLE':'U1 + bias + cutoff missing','ESTOP_OK':'Cutoff/feedback parts missing',
           'EF':'ECHO disconnected; parts missing','EL':'ECHO disconnected; parts missing','ER':'ECHO disconnected; parts missing'}
    d.text(55,162,'GPIO / terminal',17,bold=True);d.text(275,162,'Firmware signal',17,bold=True);d.text(535,162,'Exact proposed endpoint chain',17,bold=True);d.text(1260,162,'Electrical status / requirement',17,bold=True)
    for i,(name,b) in enumerate(D['gpio_bindings'].items()):
        d.svg.append(f'<g data-gpio="{b["gpio"]}" data-signal="{name}">')
        y=196+i*42;n=N[b['net']];d.line([(50,y+22),(1630,y+22)],'#dce2e8',1)
        d.text(55,y,'GPIO'+str(b['gpio']),17,bold=True);d.text(275,y,name,16,COL[n['kind']]);d.text(535,y,destinations[name],16)
        d.text(1260,y,gpio_route_status(D,name),13,color='#995b00',bold=True)
        d.svg[-1]=d.svg[-1].replace('<text ','<text data-role="route-status" ',1)
        note=notes.get(name,'U1 + bias parts missing' if 'buffer_in' in b else 'Carrier/pulls unverified; HOLD')
        d.text(1260,y+14,note,11,color='#995b00')
        d.svg[-1]=d.svg[-1].replace('<text ','<text data-role="route-note" ',1)
        d.svg.append('</g>')
    d.lines(55,910,'5V/VIN: only V5_MCU after OV1 and actual-board qualification. 3V3: E-stop dry feedback + U2 only. GND: logic return to BUCK1 OUT-. Never feed 5V into a GPIO or 3V3 pin.',width=135,size=16,leading=25)
    d.lines(55,985,'Unused: GPIO26, GPIO39/VN, GPIO4. Reserve GPIO1/3 for serial, GPIO0/2/5/12/15 boot straps, GPIO6-11 flash. Keep EN/reset under onboard control; no JTAG on GPIO13/14. ESP32-CAM remains disconnected.',width=135,size=16,leading=25)
    d.save('esp32_pinout')

def sensors():
    d=Drawing('HC-SR04: dividers plus powered-off ECHO isolation','U2 = SN74LVC3G34DCU; supply from MCU 3V3, not sensor 5V. Same GPIOs. Verify actual pulse levels/edges before connection.')
    for idx,(ref,trig,echo,inp,out,rt,rb,ui,uo,rp) in enumerate([('US_F',32,34,13,7,23,24,1,7,30),('US_L',33,35,15,5,25,26,3,5,31),('US_R',13,36,17,3,27,28,6,2,32)]):
        y=170+idx*275
        d.card(45,y,360,200,'ESP1 / '+ref,[f'GPIO{trig} TRIG 0/3.3V',f'GPIO{echo} <- U2.{uo} output',f'R{rp} 100k GPIO-to-GND','U2.8 -> ESP1.3V3','U2.4 -> ESP1.GND'])
        d.card(540,y,330,65,f'U1.{inp} -> U1.{out}',[],True)
        d.card(1200,y,425,200,ref+' HC-SR04',['VCC -> protected V5_LOGIC','GND -> BUCK2 OUT- / GND',f'TRIG <- U1.{out}',f'ECHO -> R{rt}.1','No direct ECHO-to-GPIO'])
        d.line([(405,y+42),(540,y+42)],COL['sensor'],2,True)
        d.line([(870,y+42),(1200,y+42)],COL['sensor'],2,True)
        d.text(925,y+29,'TRIG 0/5V',14,COL['sensor'])
        d.line([(1200,y+120),(1055,y+120)],COL['sensor'],2,True)
        d.rect(905,y+105,150,30,fill='#fff2d8');d.text(916,y+125,f'R{rt}: 2.2k 1%',14)
        d.line([(905,y+120),(805,y+120),(735,y+120)],COL['sensor'],2,True);d.dot(805,y+120,COL['sensor'])
        d.card(465,y+90,270,65,f'U2.{ui} A -> U2.{uo} Y',[],True)
        d.line([(465,y+120),(405,y+120)],COL['sensor'],2,True)
        d.line([(805,y+120),(805,y+165)],COL['ground'],2,True)
        d.rect(740,y+165,130,28,fill='#fff2d8');d.text(749,y+185,f'R{rb}: 3.3k 1%',13)
        d.line([(805,y+193),(805,y+220)],COL['ground'],2,True)
        d.text(825,y+224,'GND; divider nominal 3.0V',14)
    d.lines(50,1020,'C_U2: 100nF U2.8-to-U2.4. U2 inputs: HIGH >=2.0V, LOW <=0.8V; edge rate <=10ns/V at 3.3V +/-0.3V. Keep divider-to-U2 traces short. Scope actual sensor cable and pulse shape. U2 outputs follow MCU supply; power-off Ioff limits backfeed.',width=150,size=14,leading=20)
    d.save('sensor_wiring')

def power():
    d=Drawing('Battery and power distribution','High-current paths are thick red/black. All fuse, wire, coil, protection and motor-current ratings are TBD; no battery operation is approved.')
    for x,w,title,lines,missing in [(55,240,'BT1 3S LiPo',['11.1V nominal / 3300mAh','Up to 12.6V: verify label'],False),(345,160,'F0 main fuse',['A / DC interrupt TBD'],True),(555,160,'S0 master',['DC-rated isolator'],True),(765,300,'P1 protection',['High-side cell UV/OV/OCP','CELL0..3 mapping BLOCKED'],True),(1155,400,'TB_POS',['PACK_PROTECTED distribution'],True)]:
        d.card(x,175,w,100,title,lines,missing)
    for a,b,netname in [(295,345,'PACK_RAW'),(505,555,'PACK_FUSED'),(715,765,'PACK_ISOLATED'),(1065,1155,'PACK_PROTECTED')]:
        d.line([(a,225),(b,225)],COL['power_hc'],6,True)
        d.text(a,305,netname,12,COL['power_hc'])
    d.line([(1555,225),(1600,225),(1600,1015)],COL['power_hc'],6,True)
    d.card(1190,355,330,85,'K1 main NO',['Independent motor disconnect'],True)
    d.line([(1600,397),(1520,397)],COL['power_hc'],6,True)
    d.line([(1190,397),(1110,397),(1110,745)],COL['power_hc'],6,True)
    d.text(950,375,'MOTOR_SWITCHED',14,COL['power_hc'])
    for y,fuse,driver,rail,motors in [(475,'FL','DRV_L','LEFT_SUPPLY','M1/M2 left wheels'),(595,'FR','DRV_R','RIGHT_SUPPLY','M3/M4 right wheels'),(715,'FA','DRV_A','AUX_SUPPLY','M5/M6 brushes + M7 conveyor')]:
        d.card(790,y-40,260,80,fuse+' branch fuse',['Rating/coordination TBD'],True)
        d.card(370,y-40,340,80,driver,[rail+(' -> Vs / +12V' if driver=='DRV_A' else ' -> B+')])
        d.card(55,y-40,250,80,'Motor loads',[motors])
        d.line([(1110,y),(1050,y)],COL['power_hc'],6,True);d.line([(790,y),(710,y)],COL['power_hc'],6,True)
        d.line([(370,y),(305,y)],COL['motor'],6,True)
    for y,i,load in [(870,1,'ESP1 5V/VIN only'),(1005,2,'Sensors / U1 / driver logic')]:
        d.card(1235,y-40,285,80,'F'+str(i)+' input fuse',['A / DC rating TBD'],True)
        d.card(895,y-40,275,80,'BUCK'+str(i)+' LM2596',['Adjust 5.00V before load'])
        d.card(540,y-40,290,80,'OV'+str(i)+' rail protection',['OVP/OCP + power-good'],True)
        d.card(55,y-40,420,80,'V5_MCU' if i==1 else 'V5_LOGIC',[load])
        for a,b in [(1600,1520),(1235,1170),(895,830),(540,475)]:d.line([(a,y),(b,y)],COL['power_lc'],3,True)
    d.text(55,1095,'All returns -> TB_GND. Heavy driver returns; logic returns via buck OUT-. FK/coil chain: emergency_stop sheet. Do not parallel +5V outputs.',14)
    d.save('power_distribution')

def emergency():
    d=Drawing('Independent emergency cutoff and manual power-arm','Functional contact roles only; actual contactor/supervisor/contact-block parts and terminal numbers must be selected and verified.')
    d.text(55,166,'1. Coil seal-in: independent of ESP32; S3 must be released for normal no-auto-restart behavior.',18,bold=True)
    for x,w,title,lines in [(45,170,'FK coil fuse',['Protected pack','Coil voltage TBD']),(280,190,'OV1 PG NO',['MCU rail healthy','Isolated contact']),(535,190,'OV2 PG NO',['Logic rail healthy','Isolated contact']),(790,190,'S2 COIL NC',['Latching E-stop','Separate contact'])]:
        d.card(x,250,w,105,title,lines,True)
    for a,b in [(215,280),(470,535),(725,790)]:d.line([(a,302),(b,302)],COL['power_lc'],3,True)
    d.card(1060,215,220,80,'S3 power-ARM NO',['Momentary; not serial ARM'],True)
    d.card(1060,430,220,80,'K1 AUX_HOLD NO',['Separate seal-in contact'],True)
    d.line([(980,302),(1020,302),(1020,255),(1060,255)],COL['power_lc'],3,True)
    d.line([(1020,302),(1020,470),(1060,470)],COL['power_lc'],3,True)
    d.line([(1280,255),(1320,255),(1320,470),(1280,470)],COL['power_lc'],3,True)
    d.line([(1320,302),(1400,302)],COL['power_lc'],3,True)
    d.card(1400,250,220,105,'K1 coil A1/A2',['Coil range/current TBD','Z_COIL across A1/A2'],True)
    d.text(1400,392,'A2 -> TB_GND',16)
    d.lines(55,550,'K1 MAIN_NO powers FL/FR/FA only. Stop opens coil + EN; K1 drops its seal-in and isolated feedback. Release alone does not restore power with S3 released. Held S3 / welded contacts are not covered by this functional single-channel circuit.',width=145,size=16,leading=24)
    d.text(55,680,'2. Firmware healthy input: HIGH only when E-stop released AND K1 closed.',18,bold=True)
    d.card(55,720,250,85,'ESP1 3V3',['Never 5V / coil voltage'])
    d.card(400,720,280,85,'S2 SENSE NC',['Isolated low-current contact'],True)
    d.card(775,720,315,85,'K1 AUX_SENSE NO',['Separate from coil seal-in'],True)
    d.card(1195,720,430,85,'GPIO27 / ESTOP_OK',['R29 10k -> GND + internal pull-down'])
    for a,b in [(305,400),(680,775),(1090,1195)]:d.line([(a,762),(b,762)],COL['control'],2,True)
    d.text(55,862,'K1-open boot intentionally latches ESTOP. Later: EN measured LOW -> deliberate power-ARM -> GPIO27 HIGH -> RESET -> ARM.',16)
    d.text(55,927,'3. Shared enable: physical S2 contact opens every driver EN, independently of software.',18,bold=True)
    d.card(55,957,275,90,'GPIO14 -> U1.11',['R5 2.2k -> GND'])
    d.card(425,957,270,90,'U1.9 EN 0/5V',['Non-inverting AHCT'],True)
    d.card(790,957,280,90,'S2 EN NC',['Separate isolated contact'],True)
    d.card(1165,957,460,90,'EN_DRIVER_5V',['4 BTS enables + L298 ENA/ENB','Six local 10k pull-downs'],True)
    for a,b in [(330,425),(695,790),(1070,1165)]:d.line([(a,1002),(b,1002)],COL['control'],2,True)
    d.save('emergency_stop')

def drivers():
    d=Drawing('Motor-driver connections: seven motors','Each orange bundle represents two separate motor conductors. Exact per-terminal nets/fuses are shown in the complete schematic and CSV.')
    rows=[(180,'DRV_L','LEFT_SUPPLY','RPWM <- U1.18 / LPWM <- U1.16',[(1,'M+ / M-'),(2,'M+ / M-')]),(455,'DRV_R','RIGHT_SUPPLY','RPWM <- U1.14 / LPWM <- U1.12',[(3,'M+ / M-'),(4,'M+ / M-')]),(730,'DRV_A','AUX_SUPPLY','IN1/2 GPIO21/22; IN3/4 GPIO23/25',[(5,'OUT1 / OUT2'),(6,'OUT1 / OUT2'),(7,'OUT3 / OUT4')])]
    for y,ref,rail,controls,motors in rows:
        isaux=ref=='DRV_A'
        lines=([rail+' -> Vs; GND -> power return','5V_LOGIC external input -> V5_LOGIC',controls,'ENA/ENB <- EN_DRIVER_5V','Remove EN jumpers; currents/thermal TBD'] if isaux else
               [rail+' -> B+','B- -> TB_GND; dedicated branch-rated power return',
                'GND/B- internal bond: VERIFY; no extra return wire','VCC -> qualified V5_LOGIC',controls,
                'R_EN and L_EN <- EN_DRIVER_5V','Remove EN jumpers; currents/thermal TBD'])
        d.svg.append(f'<g data-driver="{ref}">')
        d.card(55,y,650,205,ref+' | '+C[ref]['name'],lines)
        d.svg.append('</g>')
        for j,(i,ports) in enumerate(motors):
            yy=y+j*(72 if isaux else 100)
            d.card(1130,yy,495,65,'M'+str(i)+' | '+C['M'+str(i)]['name'],[])
            d.line([(705,y+42+j*65),(810,y+42+j*65),(810,yy+32),(1130,yy+32)],COL['motor'],6,True)
            d.text(835,yy+20,ports+'; A via FM'+str(i),14,COL['motor'])
            d.text(1142,yy+50,'A: fused output; B: bridge return',13)
    d.lines(55,1042,'M1/M2 and M3/M4 are parallel wheel pairs. M5/M6 are parallel on channel A; M7 is channel B. No motor lead to GND/chassis. Conveyor voltage and all motor running/start/stall currents remain unverified.',width=145,size=16,leading=24)
    d.save('motor_drivers')

def physical():
    d=Drawing('Physical harness layout - placement suggestion','Not to scale or connector orientation. Bundles are separate labeled conductors; use the full terminal/connection tables before fitting any wire.')
    for x,ref,desc in [(55,'US_F','Front: GPIO32 / GPIO34'),(620,'US_L','Left: GPIO33 / GPIO35'),(1185,'US_R','Right: GPIO13 / GPIO36')]:
        d.card(x,160,440,95,ref+' HC-SR04',[desc,'VCC/GND plus protected TRIG/ECHO'])
    d.card(560,300,570,100,'Sensor conditioning / logic harness',['3 ECHO dividers + U2; U1 triggers','ECHO parts missing: do not bypass'],True)
    d.line([(275,255),(275,330),(560,330)],COL['sensor'],2,True)
    d.line([(840,255),(840,300)],COL['sensor'],2,True)
    d.line([(1405,255),(1405,330),(1130,330)],COL['sensor'],2,True)
    d.text(290,315,'H-SF: four separate wires',13,COL['sensor'])
    d.text(850,280,'H-SL: four separate wires',13,COL['sensor'])
    d.text(1165,315,'H-SR: four separate wires',13,COL['sensor'])
    d.card(620,470,450,135,'ESP1 + U1 logic area',['Existing 16 GPIO assignments preserved','U1/U2 interfaces / local pull-downs','No motor-current return in this area'])
    d.line([(840,400),(840,470)],COL['sensor'],2,True)
    for y,ref,m1,m2 in [(475,'DRV_L','M1 left front','M2 left rear'),(755,'DRV_R','M3 right front','M4 right rear')]:
        d.card(55,y-35,245,155,ref,['5V logic / common GND','Fused switched motor supply','Two PWM + two EN terminals'])
        for yy,title in [(y-55,m1),(y+65,m2)]:d.card(355,yy,240,80,title,['A fuse / B return'])
        d.line([(300,y),(355,y-15)],COL['motor'],6,True);d.line([(300,y+70),(355,y+105)],COL['motor'],6,True)
        d.line([(620,520),(300,520)],COL['control'],2,True) if ref=='DRV_L' else d.line([(620,570),(605,570),(605,800),(300,800)],COL['control'],2,True)
        d.text(355,535 if ref=='DRV_L' else 815,'H-L: 16/17 + EN' if ref=='DRV_L' else 'H-R: 18/19 + EN',13,COL['control'])
    d.card(1130,475,250,170,'DRV_A / one L298N',['A: both brushes','B: conveyor','GPIO21/22/23/25','ENA/ENB shared'])
    for yy,title in [(460,'M5 brush 1'),(580,'M6 brush 2'),(730,'M7 conveyor')]:
        d.card(1435,yy,190,75,title,['A fuse / B return'])
        start={460:515,580:565,730:635}[yy]; xx=1410 if yy==580 else 1395
        d.line([(1380,start),(xx,start),(xx,yy+35),(1435,yy+35)],COL['motor'],6,True)
        d.text(1445,yy+98,'A / B via FM'+{460:'5',580:'6',730:'7'}[yy],12,COL['motor'])
    d.line([(1070,535),(1130,535)],COL['control'],2,True)
    d.card(620,705,450,135,'Protected power + E-stop panel',['S2 / S3 / K1 + coil clamp','Fuses, P1 and OV1/OV2: select parts','BUCK1 5V MCU / BUCK2 5V logic'],True)
    d.line([(845,705),(845,605)],COL['power_lc'],3,True)
    d.line([(1070,770),(1100,770),(1100,610),(1130,610)],COL['power_hc'],6,True)
    d.line([(620,790),(310,790),(310,590),(300,590)],COL['power_hc'],6,True)
    d.line([(620,820),(300,820)],COL['power_hc'],6,True)
    d.card(55,940,410,100,'BT1 + adjacent F0',['Insulated restrained LiPo','Main + balance unplugged for wiring'])
    d.card(620,940,450,100,'TB_GND power-return star',['Heavy driver returns / coil return','Logic grounds via buck negative paths'],True)
    d.card(1215,940,410,100,'Reserved ESP32-CAM',['All pins disconnected','No supply/current budget allocated'])
    d.line([(260,940),(260,900),(760,900),(760,840)],COL['power_hc'],6,True)
    d.line([(465,1010),(620,1010)],COL['ground'],6,True)
    d.line([(845,940),(845,840)],COL['ground'],6,True)
    d.text(855,892,'H-GND: dedicated power returns',13,COL['ground'])
    d.lines(55,1080,'Keep high-current orange/red/black wiring separate from blue/green signal harnesses. Use insulated rated terminals; no breadboard motor paths. Exact wire gauge, length, connectors, routing and suppression remain release items.',width=155,size=14,leading=20)
    d.save('physical_wiring')

def ground_source(node):
    ref,pin=node.split('.',1)
    if node in ('DRV_L.GND','DRV_R.GND'):return ref+'.B-','INTERNAL_VERIFY'
    if node in ('BUCK1.OUT-','BUCK2.OUT-'):return ref+'.IN-','INTERNAL_VERIFY'
    if node=='ESP1.GND':return 'BUCK1.OUT-','WIRE'
    if node in ('U1.1','U1.19'):return 'U1.10','WIRE'
    if node=='U2.4':return 'ESP1.GND','WIRE'
    if ref=='C_U2':return 'U2.4','WIRE'
    if node=='U1.10' or ref.startswith('US_') or ref=='OV2':return 'BUCK2.OUT-','WIRE'
    if ref=='OV1':return 'BUCK1.OUT-','WIRE'
    if ref=='Z_COIL':return 'K1.A2','WIRE'
    if ref in ('C_U1',):return 'U1.10','WIRE'
    if ref in ('C_F','C_L','C_R'):return {'C_F':'US_F.GND','C_L':'US_L.GND','C_R':'US_R.GND'}[ref],'WIRE'
    if ref in ('C_BL','C_BR','C_BA','Z_L','Z_R','Z_A'):return {'C_BL':'DRV_L.B-','C_BR':'DRV_R.B-','C_BA':'DRV_A.GND','Z_L':'DRV_L.B-','Z_R':'DRV_R.B-','Z_A':'DRV_A.GND'}[ref],'WIRE'
    if ref.startswith('R') and ref[1:].isdigit():
        i=int(ref[1:])
        if i<=8:return 'U1.10','WIRE'
        if i<=12:return 'DRV_A.GND','WIRE'
        if i in (13,14,19,20):return 'DRV_L.GND','WIRE'
        if i in (15,16,21,22):return 'DRV_R.GND','WIRE'
        if i in (17,18):return 'DRV_A.GND','WIRE'
        return 'ESP1.GND','WIRE'
    return 'TB_GND.BUS','WIRE'

def connection_rows():
    rows=[]
    for n in D['nets']:
        for dest in n['nodes'][1:]:
            source=n['nodes'][0];route='WIRE'
            if n['name']=='GND':source,route=ground_source(dest)
            if n['name']=='PACK_PROTECTED' and dest!='TB_POS.BUS':source='TB_POS.BUS'
            high=n['kind'] in ('power_hc','motor') or dest in ('BT1.PACK-','DRV_L.B-','DRV_R.B-','DRV_A.GND') or dest.startswith('C_B') or dest in ('Z_L.-','Z_R.-','Z_A.-')
            rows.append(dict(wire_id=f'W{len(rows)+1:03}',component=C[dest.split('.')[0]]['name'],source=label(source),destination=label(dest),net=n['name'],signal_type=n['kind'],voltage=n['voltage'],color={'#c62828':'Red','#17232c':'Black','#1565c0':'Blue','#23844b':'Green','#d87800':'Orange'}[COL[n['kind']]],conductor_class='HIGH CURRENT - size TBD' if high else 'SIGNAL / LOGIC / COIL - size TBD',status=n['status'],connection_kind=route,protection=n['protection'],verification=n['verify']))
    return rows

def csvwrite(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def detail_sheets():
    """Terminal-complete focused views use model data, never hand-written pin maps."""
    specs=[('left_bts7960','Left BTS7960 and wheel pair',['DRV_L','M1','M2','FM1','FM2']),
           ('right_bts7960','Right BTS7960 and wheel pair',['DRV_R','M3','M4','FM3','FM4']),
           ('cleaning_driver','Conditional L298N and cleaning motors',['DRV_A','M5','M6','M7','FM5','FM6','FM7']),
           ('seven_motors','All seven motor terminals',['M1','M2','M3','M4','M5','M6','M7']),
           ('logic_enable','Buffers and default-low interface',['U1','U2','R5','R13','R14','R15','R16','R17','R18','R30','R31','R32'])]
    names=[]
    for name,title,refs in specs:
        d=Drawing(title,'Equal net names join. Exact connections and protection: assembly_connections sheets / READY_TO_WIRE.md. Ratings remain HOLD.')
        ys=[148]*3
        for ref in refs:
            col=min(range(3),key=lambda k:ys[k])
            assert ys[col]+component_height(ref)<1110, ('Detail sheet overflow',name,ref)
            ys[col]+=component(d,ref,42+col*534,ys[col])+14
        d.save(name);names.append(name)
    return names

def assembly_sheets(rows):
    names=[]
    for first in range(0,len(rows),22):
        name='assembly_connections_'+str(first//22+1).zfill(2)
        d=Drawing('Assembly: SOURCE PIN -> DESTINATION PIN / '+str(first//22+1),
                  'Every canonical row is shown exactly once. INTERNAL_VERIFY is an existing module bond to inspect, not a wire to add.')
        for i,r in enumerate(rows[first:first+22]):
            y=155+i*42
            d.svg.append(f'<g data-wire-id="{r["wire_id"]}" data-source="{html.escape(r["source"].split()[0])}" data-destination="{html.escape(r["destination"].split()[0])}">')
            d.text(55,y,r['wire_id'],14,bold=True)
            d.text(125,y,r['source']+' -> '+r['destination'],15,COL[r['signal_type']],True)
            d.text(125,y+17,r['net']+' | '+r['connection_kind']+' | '+r['voltage'],12)
            d.text(1370,y,r['status'],12,color='#995b00')
            d.line([(50,y+23),(1630,y+23)],'#dce2e8',1)
            d.svg.append('</g>')
        d.save(name);names.append(name)
    return names

def tables(rows):
    csvwrite(ROOT/'electrical/connections.csv',rows)
    terminals=[]
    for ref,c in C.items():
        for pin,function in c['pins'].items():
            node=ref+'.'+pin;n=PIN_NET.get(node)
            terminals.append(dict(component=ref,name=c['name'],terminal=pin,function=function,net=n['name'] if n else 'NO_CONNECT',voltage=n['voltage'] if n else 'None assigned',status=n['status'] if n else 'NO_CONNECT',inventory='EXISTING / UNVERIFIED' if c['in_inventory'] else 'ADDITIONAL / NOT CONFIRMED',note=D['no_connect'].get(node,c['note'])))
    csvwrite(ROOT/'electrical/terminal_map.csv',terminals)
    csvwrite(ROOT/'electrical/bom.csv',[dict(reference=ref,name=c['name'],value=c['value'],inventory='EXISTING / UNVERIFIED' if c['in_inventory'] else 'ADDITIONAL / SELECT OR BUY',footprint='UNASSIGNED',notes=c['note']) for ref,c in C.items()])
    md=(ROOT/'electrical/final_wiring_intro.md').read_text()
    md+='\n| ID | Component | Source terminal | Destination terminal | Signal / expected voltage | Status / route | Required protection | Verification |\n|---|---|---|---|---|---|---|---|\n'
    esc=lambda s:str(s).replace('|','/').replace('\n',' ')
    for r in rows:
        md+='| '+' | '.join(esc(v) for v in (r['wire_id'],r['component'],r['source'],r['destination'],r['signal_type']+'; '+r['voltage'],r['status']+'; '+r['connection_kind'],r['protection'],r['verification']))+' |\n'
    md+='\n## No-connect / reserved terminal list\n\n| Terminal | Disposition |\n|---|---|\n'
    md+=''.join('| '+label(node)+' | '+note+' |\n' for node,note in D['no_connect'].items())
    md+='\n## Component / terminal legend\n\nAll physical connector positions are to be verified on the actual part. Generic safety assembly ports cannot be mapped until selection. Complete per-terminal voltage/status detail: `electrical/terminal_map.csv`.\n\n| Reference | Component | Value / selection | Availability |\n|---|---|---|---|\n'
    md+=''.join('| '+ref+' | '+c['name']+' | '+(c['value'] or 'Exact module variant TBD')+' | '+('Existing, unverified' if c['in_inventory'] else '**Additional / missing or unselected**')+' |\n' for ref,c in C.items())
    (ROOT/'docs/FINAL_WIRING.md').write_text(md)
    styles=getSampleStyleSheet();styles.add(ParagraphStyle('Cell',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=0,wordWrap='CJK'))
    cell=lambda s:Paragraph(html.escape(txt(s)),styles['Cell'])
    data=[[cell(s) for s in ['ID / status','Source -> destination','Type / voltage / color','Protection','Verification']]]
    for r in rows:
        data.append([cell(r['wire_id']+' / '+r['status']+' / '+r['connection_kind']),cell(r['source']+' -> '+r['destination']+' / '+r['net']),cell(r['signal_type']+' / '+r['voltage']+' / '+r['color']),cell(r['protection']),cell(r['verification'])])
    doc=SimpleDocTemplate(str(OUT/'pin_to_pin_table.pdf'),pagesize=landscape(A3),leftMargin=24,rightMargin=24,topMargin=30,bottomMargin=30)
    table=LongTable(data,colWidths=[125,245,220,245,306],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef4')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#acb7c2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fffaf0')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story=[Paragraph('E2 pin-to-pin connection table - DESIGN HOLD',styles['Title']),Paragraph('All physical connections remain provisional or blocked. INTERNAL_VERIFY means inspect an existing module bond, not install another thin return. Component definitions, exact notes and release gates are in FINAL_WIRING.md.',styles['BodyText']),Spacer(1,12),table]
    doc.build(story)
    return terminals

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pages=schematics();pinout();sensors();power();emergency();drivers();physical()
    rows=connection_rows();terminals=tables(rows)
    from generate_ready_to_wire import generate
    (ROOT/'docs/READY_TO_WIRE.md').write_text(generate(rows))
    names=['physical_wiring','esp32_pinout','motor_drivers','power_distribution','sensor_wiring','emergency_stop']+detail_sheets()+assembly_sheets(rows)
    writer=PdfWriter()
    for name in ['complete_schematic']+names+['pin_to_pin_table']:writer.append(PdfReader(OUT/(name+'.pdf'),strict=True))
    write_validated_pdf(writer,OUT/'electrical_package.pdf')
    index='# Electrical diagrams E2\n\n**Design hold: no physical connection is approved.** All pages use the same `electrical/design.json`. No KiCad installation/PCB footprint/ERC verification. Generic module/safety ports are not guessed physical pin positions.\n\n'
    index+='[Combined electrical package PDF](electrical_package.pdf) / [full schematic PDF](complete_schematic.pdf) / [connection table PDF](pin_to_pin_table.pdf)\n\n'
    for name in pages+names:
        index+=f'- {name}: [SVG]({name}.svg), [PDF]({name}.pdf), [PNG preview]({name}.png)\n'
    index+='\nGenerated by `.venv/bin/python scripts/generate_wiring.py` after installing `requirements-design.txt`. Electrical model checks: `python3 scripts/check_electrical.py`.\n'
    (OUT/'INDEX.md').write_text(index)
    manifest={'revision':D['revision'],'schematic_sheets':len(pages),'diagrams':names,'wire_rows':len(rows),'terminal_rows':len(terminals),'components':len(C),'nets':len(N),'physical_release':'HOLD','kicad_available':False,'footprints':'NONE ASSIGNED','pdf_pages':len(PdfReader(OUT/'electrical_package.pdf').pages)}
    (ROOT/'electrical/export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
