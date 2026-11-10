from pathlib import Path
import copy,csv,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_system import check,main
class SystemGraph(unittest.TestCase):
 def setUp(self):
  self.model=json.loads((ROOT/'electrical/system_netlist.json').read_text());self.rows=list(csv.DictReader((ROOT/'electrical/system_connections.csv').open()))
 def test_sources_and_generated_sheets_agree(self):main()
 def move(self,node,target):
  for n in self.model['nets']:
   if node in n['nodes']:n['nodes'].remove(node)
  next(n for n in self.model['nets'] if n['name']==target)['nodes'].append(node)
 def reject(self):
  with self.assertRaises(AssertionError):check(self.model,self.rows)
 def test_camera_cannot_use_main_mcu_rail(self):self.move('CAM1.5V','V5_MCU');self.reject()
 def test_camera_cannot_take_raw_battery(self):self.move('CAM1.5V','PACK_PROTECTED');self.reject()
 def test_regulator_cannot_bypass_motor_contactor(self):self.move('BUCK3.IN+','MOTOR_SWITCHED');self.reject()
 def test_missing_camera_ground_is_rejected(self):self.move('CAM1.GND','V5_CAMERA');self.reject()
 def test_parallel_positive_regulator_outputs_rejected(self):self.move('BUCK3.OUT+','V5_LOGIC');self.reject()
 def test_duplicate_wire_id_rejected(self):self.rows.append(copy.deepcopy(self.rows[-1]));self.reject()
 def test_main_mapping_remains_frozen(self):self.model['gpio_bindings']['L_FWD']['gpio']=4;self.reject()

 def test_git_lf_checkout_is_accepted(self):
  import tempfile
  import generate_system
  old=generate_system.ROOT
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for name in ['electrical/design.json','electrical/connections.csv','include/rover_pins.h','electrical/system_design.json']:
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
   try:
    generate_system.ROOT=root
    overlay,base,rows=generate_system.load()
    self.assertEqual(len(rows),211)
   finally:generate_system.ROOT=old
 def test_frozen_csv_hash_is_portable_but_still_rejects_changes(self):
  import hashlib
  from check_team_handover import input_hash_matches
  lf=b'wire_id,source\nW001,BT1.PACK+\n';crlf=lf.replace(b'\n',b'\r\n');digest=hashlib.sha256(crlf).hexdigest()
  self.assertTrue(input_hash_matches('connections.csv',lf,digest));self.assertTrue(input_hash_matches('connections.csv',crlf,digest))
  self.assertFalse(input_hash_matches('connections.csv',lf.replace(b'BT1',b'BAD'),digest))
