"""Regress the three audit findings against real export fixtures; no hardware I/O."""
from pathlib import Path
import copy,csv,json,re,sys,unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from electrical_export_contracts import (
    check_pinout_svg, check_bts_overview_svg, check_internal_returns,
    check_classic_pdf_xref, gpio_route_status,
)
MODEL=json.loads((ROOT/'electrical/design.json').read_text())


class AuditExportRegressions(unittest.TestCase):
    def setUp(self):
        self.pinout=ET.parse(ROOT/'docs/diagrams/esp32_pinout.svg').getroot()
        self.drivers=ET.parse(ROOT/'docs/diagrams/motor_drivers.svg').getroot()
        self.pdf=(ROOT/'docs/diagrams/electrical_package.pdf').read_bytes()

    def test_generated_drawing_semantics(self):
        check_pinout_svg(self.pinout,MODEL)
        check_bts_overview_svg(self.drivers)

    def test_left_logic_header_cannot_replace_power_return(self):
        group=next(e for e in self.drivers.iter() if e.attrib.get('data-driver')=='DRV_L')
        label=next(e for e in group if e.text and 'dedicated branch-rated' in e.text)
        label.text='GND -> power return'
        with self.assertRaises(AssertionError):check_bts_overview_svg(self.drivers)

    def test_right_bond_requires_no_extra_wire_qualification(self):
        group=next(e for e in self.drivers.iter() if e.attrib.get('data-driver')=='DRV_R')
        label=next(e for e in group if e.text and 'internal bond' in e.text)
        group.remove(label)
        with self.assertRaises(AssertionError):check_bts_overview_svg(self.drivers)

    def understate(self,name):
        group=next(e for e in self.pinout.iter() if e.attrib.get('data-signal')==name)
        next(e for e in group if e.attrib.get('data-role')=='route-status').text='PROVISIONAL'
        with self.assertRaises(AssertionError):check_pinout_svg(self.pinout,MODEL)

    def test_missing_buffer_status_cannot_be_provisional(self):self.understate('L_FWD')

    def test_echo_connection_cannot_be_unblocked(self):self.understate('EF')

    def test_downstream_buffer_blocker_is_not_lost(self):
        model=copy.deepcopy(MODEL)
        next(n for n in model['nets'] if n['name']=='L_FWD_3V3')['status']='PROVISIONAL'
        self.assertEqual(gpio_route_status(model,'L_FWD'),'BLOCKED_MISSING')

    def test_generated_pdf_offsets_are_valid(self):check_classic_pdf_xref(self.pdf)

    def damaged_pdf(self):
        end=self.pdf.index(b'\n',self.pdf.index(b'\n')+1)
        marker=self.pdf[:end]
        self.assertTrue(any(v>=128 for v in marker),'Fixture must have a binary marker')
        # Reproduce the observed text-decoding/re-encoding corruption.
        return marker.decode('utf-8',errors='replace').encode('utf-8')+self.pdf[end:]

    def test_text_reencoded_pdf_header_is_rejected(self):
        with self.assertRaises(AssertionError):check_classic_pdf_xref(self.damaged_pdf())

    def test_stale_object_offsets_rejected_even_if_startxref_is_adjusted(self):
        data=self.damaged_pdf()
        shift=len(data)-len(self.pdf)
        data=re.sub(rb'(startxref\s+)(\d+)',lambda m:m[1]+str(int(m[2])+shift).encode(),data)
        with self.assertRaises(AssertionError):check_classic_pdf_xref(data)

    def test_internal_bond_is_not_an_extra_ground_wire(self):
        with (ROOT/'electrical/connections.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        check_internal_returns(rows)
        next(r for r in rows if r['connection_kind']=='INTERNAL_VERIFY')['connection_kind']='WIRE'
        with self.assertRaises(AssertionError):check_internal_returns(rows)


if __name__=='__main__':unittest.main()
