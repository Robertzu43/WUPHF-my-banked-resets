import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import package_notices


class Distribution:
    def __init__(self,root,name,files,requires=()):
        self.root=root;self.metadata={'Name':name};self.version='1.2.3';self.files=list(map(Path,files));self.requires=list(requires)
        for name,body in files.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
    def locate_file(self,path):return self.root/path


class PackageNoticesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.stdlib=self.root/'stdlib';self.stdlib.mkdir()
        (self.stdlib/'LICENSE.txt').write_text('Python runtime license',encoding='utf-8')
        self.output=self.root/'notices'
        self.addCleanup(patch.stopall)
        patch.object(package_notices.sysconfig,'get_path',return_value=str(self.stdlib)).start()
        patch.object(package_notices.sys,'base_prefix',str(self.root/'base')).start()
        self.pyinstaller=Distribution(self.root,'pyinstaller',{'pyinstaller.dist-info/licenses/COPYING.txt':b'GPL license with bootloader exception'})
    def collect(self,*others):
        with patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller,*others]):
            package_notices.collect_notices(self.output)
        return json.loads((self.output/'index.json').read_text(encoding='utf-8'))
    def test_collects_metadata_notices_without_copying_code_or_binary_files(self):
        dist=Distribution(self.root,'keyring',{
            'keyring.dist-info/licenses/LICENSE':b'MIT text',
            'keyring.dist-info/NOTICE.txt':b'Copyright notice',
            'keyring.dist-info/licenses/LICENSE.py':b'print("not a notice")',
            'keyring/licenses/LICENSE.txt':b'not package metadata',
            'keyring.dist-info/licenses/COPYING.bin':b'\x00\xff',
        },['SecretStorage>=3; sys_platform == "linux"'])
        index=self.collect(dist)
        entries={x['name']:x for x in index['distributions']}
        self.assertEqual(entries['keyring']['version'],'1.2.3')
        self.assertEqual(entries['keyring']['requires'],['SecretStorage>=3; sys_platform == "linux"'])
        contents={(self.output/p).read_text() for p in entries['keyring']['notices']}
        self.assertEqual(contents,{'MIT text','Copyright notice'})
        self.assertEqual((self.output/index['python']['notice']).read_text(),'Python runtime license')
        self.assertIn('bootloader exception',(self.output/entries['pyinstaller']['notices'][0]).read_text())
        self.assertIn('build environment',index['scope'])
        self.assertIn('native',index['limitations'])
    def test_missing_python_notice_fails_without_creating_output(self):
        (self.stdlib/'LICENSE.txt').unlink()
        with patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller]):
            with self.assertRaisesRegex(RuntimeError,'Python'):package_notices.collect_notices(self.output)
        self.assertFalse(self.output.exists())
    def test_missing_pyinstaller_notice_fails_without_creating_output(self):
        self.pyinstaller.files=[]
        with patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller]):
            with self.assertRaisesRegex(RuntimeError,'PyInstaller'):package_notices.collect_notices(self.output)
        self.assertFalse(self.output.exists())
    def test_missing_pyinstaller_distribution_fails(self):
        with patch.object(package_notices.metadata,'distributions',return_value=[]):
            with self.assertRaisesRegex(RuntimeError,'PyInstaller'):package_notices.collect_notices(self.output)
        self.assertFalse(self.output.exists())
    def test_missing_optional_notices_are_explicit_in_inventory(self):
        index=self.collect(Distribution(self.root,'unknown-package',{}))
        entry=next(x for x in index['distributions'] if x['name']=='unknown-package')
        self.assertEqual(entry['notices'],[])
        self.assertIn('unknown-package',index['missing_notices'])
