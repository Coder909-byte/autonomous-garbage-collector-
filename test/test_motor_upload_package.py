from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from package_motor_upload import export


class MotorUploadPackage(unittest.TestCase):
    def test_compiled_inventory_hashes_and_inhibited_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('bootloader.bin', 'partitions.bin', 'boot_app0.bin', 'firmware.bin'):
                (root/name).write_bytes(('TEST IMAGE '+name).encode())
            with patch('package_motor_upload.commissioning_ready', return_value=False):
                archive, manifest = export(root, root/'boot_app0.bin', root/'output')
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(len(z.namelist()), 14)
                self.assertFalse(any('secret' in name or 'camera' in name for name in z.namelist()))
                self.assertFalse(manifest['commissioning_ready'])
                self.assertEqual(manifest['expected_boot_inhibit'], 'COMMISSIONING_REQUIRED')
                self.assertIn(b'OUTPUTS INHIBITED', z.read('README_UPLOAD.txt'))
                self.assertIn(b'--port COM7 --baud 115200', z.read('README_UPLOAD.txt'))
                self.assertEqual(json.loads(z.read('manifest.json')), manifest)
                for name, digest in manifest['sha256'].items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
                self.assertEqual(z.read('firmware/firmware.bin'), (root/'firmware.bin').read_bytes())

    def test_missing_images_do_not_replace_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root/'rover_main_motor_operation.zip'
            archive.write_bytes(b'EXISTING ARCHIVE')
            with self.assertRaises(FileNotFoundError):
                export(root, root/'boot_app0.bin', root)
            self.assertEqual(archive.read_bytes(), b'EXISTING ARCHIVE')
