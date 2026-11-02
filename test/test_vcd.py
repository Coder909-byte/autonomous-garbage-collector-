"""Host tests of runtime evidence checking; fixtures are NOT Wokwi recordings."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_vcd import validate

class TraceChecks(unittest.TestCase):
    def check(self, case='auto_forward', active=(0,2), aux=(), stuck=False, unknown=False, omit=False):
        symbols='abcdefgh'
        header='\n'.join(f'$var wire 1 {s} D{i} $end' for i,s in enumerate(symbols) if not (omit and i==7))
        lines=[header,'$enddefinitions $end','#0']+[f'0{s}' for s in symbols]
        if active or aux or unknown:
            lines+=['#1','1e']+[f'1{symbols[i]}' for i in (*active,*aux)]
            if unknown: lines+=['xb']
            if not stuck: lines+=['#2']+[f'0{symbols[i]}' for i in active]
            lines+=['#3']+[f'1{symbols[i]}' for i in active]
            lines+=['#4','0e']+[f'0{s}' for s in symbols]
        lines+=['#5']
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'synthetic.vcd'; p.write_text('\n'.join(lines))
            return validate(p,case)
    def test_forward_pwm(self): self.assertEqual([0,2],self.check()['wheel_pwm_channels'])
    def test_left_pwm(self): self.assertEqual([1,2],self.check('auto_left',(1,2))['wheel_pwm_channels'])
    def test_brush_independence(self): self.assertEqual([5],self.check('brushes_only',aux=(5,))['aux_channels'])
    def test_conveyor_independence(self): self.assertEqual([6],self.check('conveyor_only',aux=(6,))['aux_channels'])
    def test_blocked_remains_disabled(self): self.assertEqual([],self.check('obstacle_no_path',())['wheel_pwm_channels'])
    def test_opposing_channels_rejected(self):
        with self.assertRaises(ValueError): self.check(active=(0,1,2))
    def test_unknown_enabled_signal_rejected(self):
        with self.assertRaises(ValueError): self.check(unknown=True)
    def test_stuck_high_is_not_pwm(self):
        with self.assertRaises(ValueError): self.check(stuck=True)
    def test_missing_channel_rejected(self):
        with self.assertRaises(ValueError): self.check(omit=True)
    def test_wrong_auxiliary_rejected(self):
        with self.assertRaises(ValueError): self.check('brushes_only',aux=(6,))

if __name__=='__main__': unittest.main()
