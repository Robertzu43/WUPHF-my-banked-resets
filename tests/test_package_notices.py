import json
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import package_notices


class SourceResponse(io.BytesIO):
    def geturl(self):return 'https://codeload.github.com/python/cpython/tar.gz/refs/tags/v3.11.14'


def source_archive(version='3.11.14',files=None):
    files=files if files is not None else {
        'Doc/license.rst':b'Licenses and Acknowledgements for Incorporated Software\nMersenne Twister notice',
        'Modules/_sha3/LICENSE':b'MIT SHA3 notice',
        'Modules/example.c':b'not a notice',
    }
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as bundle:
        for name,body in files.items():
            entry=tarfile.TarInfo(f'cpython-{version}/{name}');entry.size=len(body)
            bundle.addfile(entry,io.BytesIO(body))
    return buffer.getvalue()


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
        patch.object(package_notices.platform,'python_version',return_value='3.11.14').start()
        self.download=patch.object(package_notices.urllib.request,'urlopen',side_effect=lambda *args,**kwargs:SourceResponse(source_archive())).start()
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

    def test_linux_collects_matching_native_package_copyright_and_lists_uncollected_binaries(self):
        import subprocess
        package=self.root/'WUPHF';package.mkdir()
        library=package/'libexample.so.1';library.write_bytes(b'\x7fELFnative library')
        (package/'WUPHF').write_bytes(b'\x7fELFbootloader')
        (package/'not-a-binary.txt').write_text('plain text')
        installed=self.root/'installed.so';installed.write_bytes(library.read_bytes())
        docs=self.root/'doc';(docs/'example').mkdir(parents=True)
        (docs/'example'/'copyright').write_text('Example native copyright')
        def query(command,**kwargs):
            body=(f'example:amd64: {installed}\n' if command[1]=='--search' and command[2].endswith('libexample.so.1') else
                  'example:amd64 1.2.3' if command[1]=='--show' else '')
            return subprocess.CompletedProcess(command,0,stdout=body,stderr='')
        with patch.object(package_notices.sys,'platform','linux'),patch.object(package_notices.shutil,'which',return_value='/usr/bin/dpkg-query'),patch.object(package_notices,'NATIVE_DOCS',docs),patch.object(package_notices.subprocess,'run',side_effect=query),patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller]):
            index=package_notices.collect_notices(self.output,package)
        entries={entry['binary']:entry for entry in index['native_binaries']}
        self.assertEqual(set(entries),{'WUPHF','libexample.so.1'})
        self.assertEqual(entries['libexample.so.1']['packages'],['example:amd64 1.2.3'])
        self.assertEqual((self.output/entries['libexample.so.1']['notices'][0]).read_text(),'Example native copyright')
        self.assertEqual(index['uncollected_native_binaries'],['WUPHF'])

    def test_native_package_file_must_match_bundled_bytes(self):
        import subprocess
        package=self.root/'WUPHF';package.mkdir();(package/'libexample.so').write_bytes(b'\x7fELFbundled')
        other=self.root/'system.so';other.write_bytes(b'\x7fELFdifferent')
        copies={}
        with patch.object(package_notices.sys,'platform','linux'),patch.object(package_notices.shutil,'which',return_value='dpkg-query'),patch.object(package_notices.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout=f'example: {other}\n')):
            inventory=package_notices.native_notices(package,copies)
        self.assertEqual(inventory[0]['notices'],[]);self.assertEqual(copies,{})

    def test_native_binaries_are_explicit_when_os_metadata_is_unavailable(self):
        package=self.root/'WUPHF';package.mkdir();(package/'library.dll').write_bytes(b'MZbinary')
        with patch.object(package_notices.sys,'platform','win32'):
            inventory=package_notices.native_notices(package,{})
        self.assertEqual(inventory[0]['binary'],'library.dll')
        self.assertEqual(inventory[0]['notices'],[])
        self.assertIn('Manual review',inventory[0]['reason'])

    def test_python_notices_use_exact_tag_and_keep_expanded_distribution_license(self):
        base=self.root/'base';base.mkdir();(base/'LICENSE.txt').write_text('Python plus Windows CRT/OpenSSL notices')
        index=self.collect()
        self.download.assert_called_once_with('https://github.com/python/cpython/archive/refs/tags/v3.11.14.tar.gz',timeout=30)
        self.assertEqual((self.output/'python/distribution-LICENSE.txt').read_text(),'Python plus Windows CRT/OpenSSL notices')
        self.assertEqual((self.output/'python/source/Modules/_sha3/LICENSE').read_text(),'MIT SHA3 notice')
        self.assertIn('Mersenne Twister',(self.output/'python/source/Doc/license.rst').read_text())
        self.assertFalse((self.output/'python/source/Modules/example.c').exists())
        self.assertEqual(len(index['python']['source']['sha256']),64)

    def test_download_failure_and_incomplete_source_fail_before_output(self):
        for response in (OSError('offline'),SourceResponse(source_archive(files={'Doc/license.rst':b'Licenses and Acknowledgements for Incorporated Software'})),SourceResponse(source_archive(files={'Modules/_sha3/LICENSE':b'MIT'}))):
            with self.subTest(response=type(response).__name__):
                self.download.side_effect=response if isinstance(response,Exception) else None
                self.download.return_value=response
                with self.assertRaisesRegex(RuntimeError,'Cannot collect required CPython'):self.collect()
                self.assertFalse(self.output.exists())

    def test_hacl_headers_are_collected_without_source_code_or_duplicate_notices(self):
        header=b'/* MIT License\nCopyright HACL contributors\nPermission granted */'
        files={'Doc/license.rst':b'Licenses and Acknowledgements for Incorporated Software',
               'Modules/_hacl/a.c':header+b'\nint implementation;',
               'Modules/_hacl/b.h':header+b'\nint declaration;',
               'Modules/_hacl/include/krml/c.h':b'/* Copyright INRIA; Licensed under Apache 2.0 and MIT Licenses. */\ncode'}
        self.download.side_effect=lambda *args,**kwargs:SourceResponse(source_archive('3.14.7',files))
        with patch.object(package_notices.platform,'python_version',return_value='3.14.7'):index=self.collect()
        text=(self.output/'python/source/HACL-NOTICES.txt').read_text()
        self.assertEqual(text.count('MIT License\n'),1);self.assertIn('Copyright INRIA',text);self.assertNotIn('implementation',text)
        self.assertIn('v3.14.7',index['python']['source']['url'])

    def test_missing_hacl_and_nonfinal_python_are_rejected(self):
        for version in ('3.14.7','3.14.7rc1'):
            self.download.side_effect=lambda *args,**kwargs:SourceResponse(source_archive('3.14.7',{'Doc/license.rst':b'Licenses and Acknowledgements for Incorporated Software'}))
            with self.subTest(version=version),patch.object(package_notices.platform,'python_version',return_value=version),self.assertRaises(RuntimeError):self.collect()
            self.assertFalse(self.output.exists())

    def test_build_provenance_links_transformed_homebrew_runtime_and_bootloader(self):
        package=self.root/'WUPHF';internal=package/'_internal';internal.mkdir(parents=True)
        cellar=self.root/'Cellar';formula=cellar/'openssl@3'/'3.6.4';(formula/'lib').mkdir(parents=True)
        original=formula/'lib'/'libcrypto.3.dylib';original.write_bytes(b'\xfe\xed\xfa\xcfOriginal Mach-O')
        (formula/'LICENSE.txt').write_text('OpenSSL Apache license');(formula/'README.txt').write_text('not a license')
        binary=internal/'libcrypto.3.dylib';binary.write_bytes(b'\xfe\xed\xfa\xcfRelocated signed Mach-O')
        extension=self.stdlib/'lib-dynload'/'_random.so';extension.parent.mkdir();extension.write_bytes(b'original')
        (internal/'_random.so').write_bytes(b'\xfe\xed\xfa\xcfextension');(package/'WUPHF').write_bytes(b'\xfe\xed\xfa\xcfbootloader')
        (internal/'unknown.dylib').write_bytes(b'\xfe\xed\xfa\xcfunknown')
        toc=self.root/'COLLECT-00.toc';toc.write_text(repr(([('libcrypto.3.dylib',str(original),'BINARY'),('_random.so',str(extension),'EXTENSION'),('WUPHF',str(self.root/'build-executable'),'EXECUTABLE')],)))
        with patch.object(package_notices.sys,'platform','darwin'),patch.object(package_notices,'HOMEBREW_CELLARS',(cellar,)),patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller]):
            index=package_notices.collect_notices(self.output,package,toc)
        entries={entry['binary']:entry for entry in index['native_binaries']}
        native=entries['_internal/libcrypto.3.dylib']
        self.assertEqual(native['packages'],['Homebrew openssl@3 3.6.4']);self.assertEqual(native['build_source'],str(original.resolve()))
        self.assertEqual((self.output/native['notices'][0]).read_text(),'OpenSSL Apache license')
        self.assertIn('python/source/Doc/license.rst',entries['_internal/_random.so']['notices'])
        self.assertEqual(entries['WUPHF']['notices'],['pyinstaller-1.2.3/licenses/COPYING.txt'])
        self.assertEqual(index['uncollected_native_binaries'],['_internal/unknown.dylib'])

    def test_homebrew_name_alone_never_substitutes_for_build_provenance(self):
        package=self.root/'WUPHF';package.mkdir();(package/'libcrypto.3.dylib').write_bytes(b'\xfe\xed\xfa\xcfunknown')
        with patch.object(package_notices.sys,'platform','darwin'):
            inventory=package_notices.native_notices(package,{})
        self.assertEqual(inventory[0]['notices'],[])

    def test_build_record_cannot_point_outside_package(self):
        package=self.root/'WUPHF';package.mkdir();toc=self.root/'COLLECT-00.toc'
        toc.write_text(repr(([('../../escape',str(self.stdlib/'_random.so'),'EXTENSION')],)))
        with patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller]),self.assertRaisesRegex(ValueError,'escapes package'):
            package_notices.collect_notices(self.output,package,toc)
        self.assertFalse(self.output.exists())

    def test_windows_dependency_uses_expanded_installed_license_only_with_provenance(self):
        package=self.root/'WUPHF';package.mkdir();binary=package/'vcruntime140.dll';binary.write_bytes(b'MZruntime')
        original=(self.root/'base'/'vcruntime140.dll').resolve()
        copies={'python/distribution-LICENSE.txt':b'Windows CRT notice'}
        with patch.object(package_notices.sys,'platform','win32'):
            entries=package_notices.native_notices(package,copies,{binary.resolve():(original,'BINARY')})
            unknown=package_notices.native_notices(package,copies)
        self.assertEqual(entries[0]['notices'],['python/distribution-LICENSE.txt'])
        self.assertEqual(unknown[0]['notices'],[])

    def test_source_notice_download_rejects_insecure_redirect_and_invalid_archive(self):
        insecure=SourceResponse(source_archive());insecure.geturl=lambda:'http://example.invalid/source'
        unofficial=SourceResponse(source_archive());unofficial.geturl=lambda:'https://example.invalid/source'
        for response in (insecure,unofficial,SourceResponse(b'not a tar archive')):
            self.download.side_effect=None;self.download.return_value=response
            with self.assertRaisesRegex(RuntimeError,'Cannot collect required CPython'):self.collect()
            self.assertFalse(self.output.exists())

    def test_native_wheel_notices_require_exact_distribution_file_ownership(self):
        dist=Distribution(self.root,'cryptography',{
            'cryptography/hazmat/bindings/_rust.abi3.so':b'\x7fELFwheel original',
            'cryptography.dist-info/licenses/LICENSE.APACHE':b'Apache notice',
            'cryptography.dist-info/licenses/LICENSE.BSD':b'BSD notice',
        })
        package=self.root/'WUPHF';package.mkdir()
        internal=package/'_internal';internal.mkdir()
        (internal/'owned.so').write_bytes(b'\x7fELFtransformed wheel binary')
        (internal/'unowned.so').write_bytes(b'\x7fELFunowned binary')
        owned=self.root/'cryptography/hazmat/bindings/_rust.abi3.so'
        other=self.root/'other/_rust.abi3.so';other.parent.mkdir();other.write_bytes(owned.read_bytes())
        toc=self.root/'COLLECT-00.toc'
        toc.write_text(repr(([('owned.so',str(owned),'EXTENSION'),('unowned.so',str(other),'EXTENSION')],)))
        with patch.object(package_notices.metadata,'distributions',return_value=[self.pyinstaller,dist]),patch.object(package_notices.shutil,'which',return_value=None):
            index=package_notices.collect_notices(self.output,package,toc)
        entries={entry['binary']:entry for entry in index['native_binaries']}
        self.assertEqual(entries['_internal/owned.so']['distribution'],{'name':'cryptography','version':'1.2.3'})
        self.assertEqual({(self.output/path).read_text() for path in entries['_internal/owned.so']['notices']},{'Apache notice','BSD notice'})
        self.assertEqual(index['uncollected_native_binaries'],['_internal/unowned.so'])

    def test_framework_openssl_uses_actual_linked_version_and_official_python_notice(self):
        package=self.root/'WUPHF';package.mkdir();binary=package/'libcrypto.3.dylib';binary.write_bytes(b'\xfe\xed\xfa\xcfOpenSSL')
        source=(self.root/'base/lib/libcrypto.3.dylib').resolve()
        notice='python/source/Doc/license.rst'
        copies={notice:b'For the OpenSSL 3.0 release, and later releases derived from that, the Apache License v2 applies.'}
        sources={binary.resolve():(source,'BINARY')}
        with patch.object(package_notices.sys,'platform','darwin'),patch.object(package_notices.ssl,'OPENSSL_VERSION','OpenSSL 3.0.13 30 Jan 2024'):
            entries=package_notices.native_notices(package,copies,sources)
            self.assertEqual(entries[0]['notices'],[notice])
            self.assertEqual(entries[0]['linked_openssl_version'],'OpenSSL 3.0.13 30 Jan 2024')
            unrelated=package_notices.native_notices(package,copies,{binary.resolve():((self.root/'other/libcrypto.3.dylib').resolve(),'BINARY')})
            self.assertEqual(unrelated[0]['notices'],[])
            self.assertEqual(package_notices.native_notices(package,{},sources)[0]['notices'],[])
        with patch.object(package_notices.sys,'platform','darwin'),patch.object(package_notices.ssl,'OPENSSL_VERSION','LibreSSL 3.3.6'):
            self.assertEqual(package_notices.native_notices(package,copies,sources)[0]['notices'],[])
