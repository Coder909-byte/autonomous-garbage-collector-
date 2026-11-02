"""Validate proposed-netlist fault rejection; no powered circuit is simulated."""
from pathlib import Path
import copy,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_electrical import check
MODEL=json.loads((Path(__file__).resolve().parents[1]/'electrical/design.json').read_text())
class ElectricalChecks(unittest.TestCase):
    def setUp(self): self.d=copy.deepcopy(MODEL)
    def net(self,name): return next(n for n in self.d['nets'] if n['name']==name)
    def reject(self):
        with self.assertRaises(AssertionError):check(self.d)
    def test_complete_model_is_structural_only(self): self.assertIn('unapproved',check(self.d)['result'])
    def test_direct_5v_echo_rejected(self):
        self.net('EF_SAFE')['nodes'].remove('ESP1.GPIO34');self.net('EF_RAW')['nodes'].append('ESP1.GPIO34');self.reject()
    def test_missing_echo_ground_rejected(self): self.net('GND')['nodes'].remove('R24.2');self.reject()
    def test_conflicting_gpio_rejected(self): self.d['gpio_bindings']['L_REV']['gpio']=16;self.reject()
    def test_parallel_buck_outputs_rejected(self): self.net('V5_MCU_RAW')['nodes'].append('BUCK2.OUT+');self.reject()
    def test_missing_enable_pull_rejected(self): self.net('GND')['nodes'].remove('R17.2');self.reject()
    def test_motor_cutoff_bypass_rejected(self):
        self.net('LEFT_SUPPLY')['nodes'].remove('DRV_L.B+');self.net('PACK_PROTECTED')['nodes'].append('DRV_L.B+');self.reject()
    def test_invented_fuse_rating_rejected(self): self.d['components']['F0']['value']='30 A';self.reject()
    def test_weak_gpio14_pull_rejected(self): self.d['components']['R5']['value']='10k';self.reject()
    def test_invented_board_footprint_rejected(self): self.d['components']['DRV_L']['footprint']='guessed';self.reject()
    def test_contactor_feedback_bypass_rejected(self):
        self.net('ESTOP_OK')['nodes'].remove('ESP1.GPIO27');self.net('SENSE_STOP_OK')['nodes'].append('ESP1.GPIO27');self.reject()
if __name__=='__main__':unittest.main()
