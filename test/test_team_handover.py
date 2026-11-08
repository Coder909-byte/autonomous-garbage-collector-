"""Guard handover omissions and accidental creation of extra internal-bond wires."""
from pathlib import Path
import copy
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_team_handover import load_inputs, connection_register
from check_team_handover import validate_records


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


if __name__=='__main__':unittest.main()
