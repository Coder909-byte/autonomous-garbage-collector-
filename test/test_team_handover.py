"""Guard handover omissions and accidental creation of extra internal-bond wires."""
from pathlib import Path
import copy
import csv
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_team_handover import load_inputs, connection_register, write_team_files, buy_now
from check_team_handover import validate_records, validate_measurements


class TeamHandoverContracts(unittest.TestCase):
    def setUp(self):
        _,model,self.source=load_inputs()
        self.rows=connection_register(self.source,model)

    def reject(self):
        with self.assertRaises(AssertionError):validate_records(self.source,self.rows)

    def test_complete_register_preserves_all_201_records(self):
        self.assertEqual(len(validate_records(self.source,self.rows)),201)
        self.assertEqual(sum(r['connection_kind']=='INTERNAL_VERIFY' for r in self.rows),4)

    def test_missing_connection_is_rejected(self):
        self.rows.pop();self.reject()

    def test_duplicate_connection_is_rejected(self):
        self.rows.append(copy.deepcopy(self.rows[0]));self.reject()

    def test_internal_bond_cannot_be_an_extra_wire(self):
        next(r for r in self.rows if r['wire_id']=='W046')['action']='EXTERNAL CONNECTION - gate dependent'
        self.reject()

    def test_changed_gpio_endpoint_is_rejected(self):
        next(r for r in self.rows if r['source']=='ESP1.GPIO16')['source']='ESP1.GPIO26'
        self.reject()

    def test_rating_cannot_omit_expected_voltage(self):
        self.rows[0]['required_electrical_rating']='Use any wire'
        self.reject()

    def test_verification_cannot_omit_e2_requirement(self):
        self.rows[0]['team_verification_method']='UNPOWERED FIRST; visual check only'
        self.reject()


class ReportedMeasurementContracts(unittest.TestCase):
    def setUp(self):
        self.requirements=json.loads((ROOT/'docs/team_handover/plan.json').read_text())['measurements']
        with (ROOT/'docs/team_handover/TEAM_MEASUREMENT_RECORD.csv').open(newline='') as f:
            self.rows=list(csv.DictReader(f))

    def test_reported_observations_do_not_close_full_requirements(self):
        result=validate_measurements(self.requirements,self.rows)
        self.assertEqual(result['COMPLETE - USER-REPORTED (observation only)'],12)
        self.assertEqual(result['PARTIAL - USER-REPORTED'],6)
        self.assertEqual(result['PENDING'],4)
        self.assertTrue(all(not r['manufacturer_or_trace_file'] and not r['reviewer_date'] for r in self.rows))

    def test_continuity_cannot_be_promoted_to_full_pass(self):
        next(r for r in self.rows if r['measurement_id']=='D08')['result']='PASS'
        with self.assertRaisesRegex(AssertionError,'cannot be marked PASS'):
            validate_measurements(self.requirements,self.rows)

    def test_reported_observation_cannot_lose_attribution_or_parent(self):
        for key,value in [('actual_value_unit','Verified independently'),('measurement_id','D99.U01')]:
            with self.subTest(key=key):
                rows=copy.deepcopy(self.rows);rows[-1][key]=value
                with self.assertRaises(AssertionError):validate_measurements(self.requirements,rows)

    def test_regenerating_handover_preserves_active_measurement_bytes(self):
        plan,model,source=load_inputs()
        original=(ROOT/'docs/team_handover/TEAM_MEASUREMENT_RECORD.csv').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);data=root/'docs/team_handover';data.mkdir(parents=True)
            (root/'docs/hardware_photos').mkdir()
            record=data/'TEAM_MEASUREMENT_RECORD.csv';record.write_bytes(original)
            with patch('generate_team_handover.ROOT',root),patch('generate_team_handover.DATA',data):
                write_team_files(plan,model,connection_register(source,model),{'files':[]},buy_now(model))
            self.assertEqual(record.read_bytes(),original)


if __name__=='__main__':unittest.main()
