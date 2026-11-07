import tempfile, unittest
from pathlib import Path
from wuphf.storage import load, save

class StorageTests(unittest.TestCase):
    def test_atomic_roundtrip_and_private_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            self.assertEqual(load(p, {}), {})
            save(p, {'last': 1})
            self.assertEqual(load(p, {}), {'last': 1})
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
    def test_corrupt_state_is_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';p.write_text('{')
            with self.assertRaises(ValueError): load(p,{})
    def test_lock_rejects_simultaneous_check(self):
        from wuphf.storage import check_lock
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lock'
            with check_lock(path):
                with self.assertRaises(RuntimeError):
                    with check_lock(path):pass
