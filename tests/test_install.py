import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='wuphf-install-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.home=self.root/'home space é $quote\' %'
        self.home.mkdir(mode=0o700)
        self.home_patch=patch.object(Path,'home',return_value=self.home)
        self.home_patch.start();self.addCleanup(self.home_patch.stop)
        self.assertIsNotNone(importlib.util.find_spec('wuphf.install'),'local bundle installer is missing')
        self.install=importlib.import_module('wuphf.install')
        self.source=self.root/'download space é'/'WUPHF'
        self.make_bundle(self.source)
        self.destination=self.home/'.local'/'opt'/'WUPHF'

    def make_bundle(self, root):
        root.mkdir(parents=True)
        public=('LICENSE','VERSION','README.md','CHANGELOG.md','docs/user-guide.md',
                'docs/google-production.md','docs/release-readiness.md','docs/releasing.md',
                'docs/images/setup-example.jpg')
        for relative in public:
            for base in (root,root/'_internal'):
                target=base/relative;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text('0.2.0-beta.1\n' if relative=='VERSION' else 'public '+relative,encoding='utf-8')
        for relative,body in [('WUPHF',b'not an executable'),('WUPHF.exe',b'not an executable'),
                              ('Start WUPHF.command',b'not a script'),('Start WUPHF.sh',b'not a script'),
                              ('_internal/wuphf/web.html',b'WUPHF'),
                              ('_internal/wuphf/translations.json',b'{"en":{}}'),
                              ('_internal/wuphf/oauth-client.json',b'{"installed":{"client_id":"public.apps.googleusercontent.com","client_secret":"public"}}'),
                              ('_internal/wuphf/assets/geist-pixel-square.woff2',b'wOF2font'),
                              ('_internal/wuphf/assets/geist-pixel-OFL.txt',b'font license'),
                              ('third-party-notices/index.json',b'{"python":{"notice":"python/LICENSE.txt"}}'),
                              ('third-party-notices/python/LICENSE.txt',b'python license')]:
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        for relative in ('WUPHF','Start WUPHF.command','Start WUPHF.sh'):(root/relative).chmod(0o755)
        (root/'build-info.json').write_text(json.dumps({'version':'0.2.0-beta.1','os':{'darwin':'macos','win32':'windows','linux':'linux'}[sys.platform]}))

    def test_installs_complete_bundle_with_spaces_unicode_modes_and_internal_symlinks(self):
        (self.source/'_internal'/'library').mkdir()
        (self.source/'_internal'/'library'/'module').write_bytes(b'library bytes')
        try:(self.source/'_internal'/'current').symlink_to('library',target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        result=self.install.install_bundle(self.source,self.destination)
        self.assertEqual(result,self.destination)
        self.assertEqual((result/'_internal'/'current'/'module').read_bytes(),b'library bytes')
        self.assertTrue((result/'_internal'/'current').is_symlink())
        self.assertEqual(os.readlink(result/'_internal'/'current'),'library')
        self.assertEqual((result/'docs'/'user-guide.md').read_bytes(),b'public docs/user-guide.md')
        if os.name!='nt':self.assertEqual(stat.S_IMODE((result/'WUPHF').stat().st_mode),0o755)
        self.assertEqual(list(self.destination.parent.iterdir()),[self.destination])


    def test_source_parent_alias_preserves_safe_internal_relative_links(self):
        (self.source/'_internal'/'library').write_bytes(b'library bytes')
        alias=self.root/'download-alias'
        try:
            alias.symlink_to(self.source.parent,target_is_directory=True)
            (self.source/'_internal'/'current').symlink_to('library')
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        self.install.install_bundle(alias/'WUPHF',self.destination)
        self.assertEqual((self.destination/'_internal'/'current').read_bytes(),b'library bytes')
        self.assertTrue((self.destination/'_internal'/'current').is_symlink())

    @unittest.skipUnless(sys.platform=='darwin','native Mac quarantine metadata test')
    def test_mac_copy_preserves_quarantine_on_folder_and_nonexecuted_fixture(self):
        import subprocess
        value='0083;00000000;WUPHF-unit-test;'
        for path in (self.source,self.source/'WUPHF'):
            subprocess.run(['/usr/bin/xattr','-w','com.apple.quarantine',value,str(path)],check=True,capture_output=True)
        with patch.dict(os.environ,{'DITTONORSRC':'1','DITTO_TEST_OPTIONS':'1'}):
            self.install.install_bundle(self.source,self.destination)
        for path in (self.destination,self.destination/'WUPHF'):
            actual=subprocess.run(['/usr/bin/xattr','-p','com.apple.quarantine',str(path)],check=True,capture_output=True,text=True).stdout.strip()
            # macOS may normalize the quarantine record while retaining its restrictions.
            self.assertEqual(int(actual.split(';')[0],16)&0x83,0x83)


    def test_windows_native_copy_boundary_retains_streams_and_directory_link_type(self):
        import ctypes
        from unittest.mock import Mock
        source=self.root/'native-source';source.mkdir()
        (source/'library').mkdir();(source/'library'/'fixture').write_bytes(b'never executed')
        try:(source/'current').symlink_to('library',target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        candidate=self.root/'native-copy';streams={str(source/'library'/'fixture'):b'ZoneId=3'}
        original_symlink=os.symlink;link_types=[]
        def copy_file(old,new,progress,data,cancel,flags):
            self.assertEqual((progress,data,cancel,flags),(None,None,None,1))
            if Path(new).exists():return 0
            shutil.copy2(old,new)
            if old in streams:streams[new]=streams[old]
            return 1
        def symlink(target,path,target_is_directory=False,**kwargs):
            link_types.append(target_is_directory)
            return original_symlink(target,path,target_is_directory=target_is_directory,**kwargs)
        kernel=Mock();kernel.CopyFileExW.side_effect=copy_file
        with patch.object(sys,'platform','win32'),patch.object(ctypes,'WinDLL',return_value=kernel,create=True),patch.object(os,'symlink',side_effect=symlink):
            self.install._copy_bundle(source,candidate)
        self.assertEqual((candidate/'current'/'fixture').read_bytes(),b'never executed')
        self.assertEqual(streams.get(str(candidate/'library'/'fixture')),b'ZoneId=3')
        self.assertEqual(link_types,[True])

    def test_windows_native_copy_failure_leaves_no_installed_app(self):
        import ctypes
        from unittest.mock import Mock
        metadata=self.source/'build-info.json';raw=json.loads(metadata.read_text());raw['os']='windows';metadata.write_text(json.dumps(raw))
        (self.source/'WUPHF.exe').chmod(0o755)
        kernel=Mock();kernel.CopyFileExW.return_value=0;codes=[]
        def windows_error(code=None):
            codes.append(code)
            return OSError(f'native stream copy denied ({code})')
        with patch.object(sys,'platform','win32'),patch.object(ctypes,'WinDLL',return_value=kernel,create=True),patch.object(ctypes,'get_last_error',return_value=5,create=True),patch.object(ctypes,'WinError',side_effect=windows_error,create=True):
            with self.assertRaisesRegex(OSError,r'native stream copy denied \(5\)'):
                self.install.install_bundle(self.source,self.destination)
        self.assertTrue(codes);self.assertEqual(set(codes),{5})
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()),[])

    def test_root_reparse_attributes_are_rejected_before_source_resolution(self):
        from types import SimpleNamespace
        original=Path.lstat
        def lstat(path,*args,**kwargs):
            info=original(path,*args,**kwargs)
            if path==self.source:return SimpleNamespace(st_mode=info.st_mode,st_file_attributes=0x400)
            return info
        with patch.object(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400,create=True),patch.object(Path,'lstat',lstat):
            with self.assertRaisesRegex(ValueError,'[Ll]ink|[Jj]unction|[Rr]eparse'):
                self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.exists())

    def test_existing_destination_root_reparse_is_not_an_identical_install(self):
        from types import SimpleNamespace
        self.destination.parent.mkdir(parents=True)
        try:self.destination.symlink_to(self.source,target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        original=Path.lstat
        def lstat(path,*args,**kwargs):
            info=original(path,*args,**kwargs)
            if path==self.destination:return SimpleNamespace(st_mode=stat.S_IFDIR|0o755,st_file_attributes=0x400)
            return info
        is_symlink=Path.is_symlink
        with patch.object(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400,create=True),patch.object(Path,'lstat',lstat),patch.object(Path,'is_symlink',lambda path:False if path==self.destination else is_symlink(path)):
            with self.assertRaises(ValueError):self.install.install_bundle(self.source,self.destination)
        self.assertTrue(self.destination.is_symlink())
        self.assertEqual((self.source/'WUPHF').read_bytes(),b'not an executable')

    @unittest.skipUnless(sys.platform=='win32','native Windows NTFS alternate-stream test')
    def test_windows_copy_preserves_download_zone_stream_without_executing_fixture(self):
        value=b'[ZoneTransfer]\r\nZoneId=3\r\n'
        Path(str(self.source/'WUPHF.exe')+':Zone.Identifier').write_bytes(value)
        self.install.install_bundle(self.source,self.destination)
        self.assertEqual(Path(str(self.destination/'WUPHF.exe')+':Zone.Identifier').read_bytes(),value)

    @unittest.skipUnless(sys.platform=='win32','native Windows directory junction test')
    def test_windows_source_and_destination_root_junctions_are_rejected(self):
        import _winapi
        source_junction=self.root/'source-junction'
        _winapi.CreateJunction(str(self.source),str(source_junction))
        with self.assertRaisesRegex(ValueError,'[Ll]ink|[Jj]unction|[Rr]eparse'):
            self.install.install_bundle(source_junction,self.destination)
        self.destination.parent.mkdir(parents=True)
        _winapi.CreateJunction(str(self.source),str(self.destination))
        with self.assertRaises(ValueError):self.install.install_bundle(self.source,self.destination)
        self.assertEqual((self.destination/'WUPHF.exe').read_bytes(),b'not an executable')
        self.assertEqual((self.source/'WUPHF.exe').read_bytes(),b'not an executable')

    def test_default_destinations_are_per_user_and_windows_requires_safe_localappdata(self):
        cases=(('darwin',{},self.home/'Library'/'Application Support'/'WUPHF'),
               ('linux',{'XDG_DATA_HOME':'/outside'},self.home/'.local'/'opt'/'WUPHF'),
               ('win32',{'LOCALAPPDATA':str(self.home/'AppData'/'Local')},self.home/'AppData'/'Local'/'WUPHF'))
        for platform,env,expected in cases:
            with self.subTest(platform=platform),patch.object(sys,'platform',platform),patch.dict(os.environ,env):
                self.assertEqual(self.install.default_destination(),expected)
        for local in ('','relative',str(self.root/'other-user')):
            with self.subTest(local=local),patch.object(sys,'platform','win32'),patch.dict(os.environ,{'LOCALAPPDATA':local}):
                with self.assertRaisesRegex(ValueError,'LOCALAPPDATA'):self.install.default_destination()

    def test_identical_install_is_noop_without_replacing_files_or_data(self):
        data=self.home/'.local'/'share'/'wuphf-resets'/'settings.json'
        data.parent.mkdir(parents=True);data.write_text('untouched private data')
        self.install.install_bundle(self.source,self.destination)
        marker=(self.destination/'WUPHF').stat()
        with patch.object(self.install,'_copy_bundle',side_effect=AssertionError('must not copy again')):
            self.assertEqual(self.install.install_bundle(self.source,self.destination),self.destination)
        self.assertEqual((self.destination/'WUPHF').stat().st_mtime_ns,marker.st_mtime_ns)
        self.assertEqual(data.read_text(),'untouched private data')


    def test_install_from_installed_location_is_validated_noop(self):
        self.install.install_bundle(self.source,self.destination)
        with patch.object(self.install,'_copy_bundle',side_effect=AssertionError('must not copy itself')):
            self.assertEqual(self.install.install_bundle(self.destination,self.destination),self.destination)
        (self.destination/'_internal'/'VERSION').unlink()
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            self.install.install_bundle(self.destination,self.destination)

    def test_configuration_filename_case_variant_is_never_read_or_copied(self):
        (self.source/'Settings.JSON').write_text('private data')
        with self.assertRaisesRegex(ValueError,'[Cc]onfiguration'):
            self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.parent.exists())

    def test_changed_existing_install_refuses_upgrade_without_changing_app_or_job(self):
        self.install.install_bundle(self.source,self.destination)
        old=(self.destination/'WUPHF').read_bytes()
        (self.source/'WUPHF').write_bytes(b'new executable')
        job=self.home/'Library'/'LaunchAgents'/'com.wuphf.resets.plist'
        job.parent.mkdir(parents=True);job.write_text('enabled job left alone')
        with self.assertRaisesRegex(ValueError,'[Uu]pgrade.*background'):
            self.install.install_bundle(self.source,self.destination)
        self.assertEqual((self.destination/'WUPHF').read_bytes(),old)
        self.assertEqual(job.read_text(),'enabled job left alone')
        self.assertEqual(list(self.destination.parent.iterdir()),[self.destination])

    def test_incomplete_bundle_is_rejected_before_creating_destination_parents(self):
        missing=('WUPHF.exe' if sys.platform=='win32' else 'WUPHF','_internal','docs/user-guide.md',
                 '_internal/docs/images/setup-example.jpg','third-party-notices/python/LICENSE.txt','build-info.json')
        for relative in missing:
            with self.subTest(missing=relative):
                damaged=self.root/('missing-'+str(missing.index(relative)))
                shutil.copytree(self.source,damaged)
                target=damaged/relative
                shutil.rmtree(target) if target.is_dir() else target.unlink()
                with self.assertRaisesRegex(ValueError,'[Ii]ncomplete'):
                    self.install.install_bundle(damaged,self.destination)
                self.assertFalse(self.destination.parent.exists())

    def test_mismatched_help_version_and_build_metadata_are_rejected(self):
        for relative,body in (('README.md','stale help'),('VERSION','\n'),
                              ('build-info.json','{"version":"other"}')):
            with self.subTest(relative=relative):
                damaged=self.root/('mismatch-'+relative.replace('.','-'))
                shutil.copytree(self.source,damaged);(damaged/relative).write_text(body)
                with self.assertRaises(ValueError):self.install.install_bundle(damaged,self.destination)
                self.assertFalse(self.destination.exists())

    def test_outside_absolute_broken_and_looping_links_are_rejected(self):
        outside=self.root/'outside';outside.write_bytes(b'do not copy')
        for target in ('../../outside',str(self.source/'WUPHF'),'missing','bad-link'):
            with self.subTest(target=target):
                link=self.source/'_internal'/'bad-link'
                try:link.symlink_to(target)
                except OSError:self.skipTest('symlinks unavailable for this Windows account')
                try:
                    with self.assertRaisesRegex(ValueError,'[Ll]ink'):
                        self.install.install_bundle(self.source,self.destination)
                    self.assertFalse(self.destination.parent.exists())
                finally:link.unlink()

    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX FIFO test')
    def test_special_file_is_rejected_without_opening_it(self):
        os.mkfifo(self.source/'pipe')
        with self.assertRaisesRegex(ValueError,'[Ss]pecial'):
            self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.parent.exists())

    def test_user_credential_file_is_rejected_without_reading_it(self):
        secret=self.source/'settings.json';secret.write_text('do not read')
        original=Path.open
        def guard(path,*args,**kwargs):
            if path==secret:raise AssertionError('installer read credential contents')
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',guard):
            with self.assertRaisesRegex(ValueError,'[Cc]onfiguration'):self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.parent.exists())

    def test_source_destination_overlap_is_rejected_in_both_directions(self):
        source=self.home/'bundle';shutil.copytree(self.source,source)
        for destination in (source/'nested',self.home):
            with self.subTest(destination=destination),self.assertRaisesRegex(ValueError,'[Oo]verlap'):
                self.install.install_bundle(source,destination)
        self.assertFalse((source/'nested').exists())

    def test_destination_outside_home_and_symlinked_parent_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'[Uu]ser|[Hh]ome'):
            self.install.install_bundle(self.source,self.root/'outside'/'WUPHF')
        actual=self.home/'actual';actual.mkdir()
        linked=self.home/'.local'
        try:linked.symlink_to(actual,target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        with self.assertRaisesRegex(ValueError,'[Ll]ink'):
            self.install.install_bundle(self.source,self.destination)
        self.assertEqual(list(actual.iterdir()),[])

    @unittest.skipIf(os.name=='nt','POSIX ownership/mode policy')
    def test_shared_or_foreign_parent_is_rejected(self):
        self.destination.parent.mkdir(parents=True);self.destination.parent.chmod(0o777)
        with self.assertRaisesRegex(ValueError,'[Oo]wned|[Pp]rivate|[Ww]ritable'):
            self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.exists())

    def test_existing_file_empty_directory_or_symlink_destination_is_never_replaced(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_text('existing file')
        with self.assertRaises(ValueError):self.install.install_bundle(self.source,self.destination)
        self.assertEqual(self.destination.read_text(),'existing file');self.destination.unlink()
        self.destination.mkdir()
        with self.assertRaises(ValueError):self.install.install_bundle(self.source,self.destination)
        self.assertEqual(list(self.destination.iterdir()),[]);self.destination.rmdir()
        try:self.destination.symlink_to(self.source,target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable for this Windows account')
        with self.assertRaises(ValueError):self.install.install_bundle(self.source,self.destination)
        self.assertTrue(self.destination.is_symlink())

    def test_interrupted_staging_cleans_only_new_staging_and_preserves_data(self):
        data=self.home/'.local'/'share'/'wuphf-resets'/'state.json'
        data.parent.mkdir(parents=True);data.write_text('private state')
        def fail_copy(source,target,**kwargs):
            Path(target).mkdir(exist_ok=True);(Path(target)/'partial').write_text('partial')
            raise OSError('simulated disk full')
        with patch.object(self.install,'_copy_bundle',side_effect=fail_copy):
            with self.assertRaisesRegex(OSError,'disk full'):self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()),[])
        self.assertEqual(data.read_text(),'private state')

    def test_corrupted_copy_is_not_promoted(self):
        copy_bundle=self.install._copy_bundle
        def corrupt(source,target):
            result=copy_bundle(source,target)
            (Path(target)/'WUPHF').write_bytes(b'corrupted copy')
            return result
        with patch.object(self.install,'_copy_bundle',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'[Cc]opy|[Cc]opied'):
                self.install.install_bundle(self.source,self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()),[])

    def test_destination_created_during_copy_is_preserved_even_when_empty(self):
        copy_bundle=self.install._copy_bundle
        def race(source,target):
            result=copy_bundle(source,target)
            self.destination.mkdir()
            return result
        with patch.object(self.install,'_copy_bundle',side_effect=race):
            with self.assertRaises((ValueError,FileExistsError)):
                self.install.install_bundle(self.source,self.destination)
        self.assertEqual(list(self.destination.iterdir()),[])
        self.assertEqual(list(self.destination.parent.iterdir()),[self.destination])

    def test_promotion_itself_never_replaces_existing_empty_directory(self):
        stage=self.home/'stage';stage.mkdir();(stage/'candidate').write_text('candidate')
        target=self.home/'target';target.mkdir()
        with self.assertRaises(FileExistsError):self.install._promote(stage,target)
        self.assertEqual((stage/'candidate').read_text(),'candidate')
        self.assertEqual(list(target.iterdir()),[])


    @unittest.skipIf(os.name=='nt','POSIX runtime capability test')
    def test_missing_native_exclusive_rename_fails_without_modifying_either_path(self):
        from types import SimpleNamespace
        stage=self.home/'stage';stage.mkdir();(stage/'candidate').write_text('candidate')
        target=self.home/'target'
        for platform in ('darwin','linux'):
            with self.subTest(platform=platform),patch.object(sys,'platform',platform),patch('ctypes.CDLL',return_value=SimpleNamespace()):
                with self.assertRaisesRegex(RuntimeError,'Atomic installation is unavailable'):
                    self.install._promote(stage,target)
            self.assertEqual((stage/'candidate').read_text(),'candidate')
            self.assertFalse(target.exists())

    def test_source_checkout_install_is_explicitly_unsupported(self):
        with patch.object(sys,'frozen',False,create=True),self.assertRaisesRegex(ValueError,'frozen.*source'):
            self.install.main()
        self.assertFalse(self.destination.parent.exists())

    def test_frozen_install_receipt_has_only_qualified_local_paths_and_version(self):
        with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(self.source/('WUPHF.exe' if sys.platform=='win32' else 'WUPHF'))),patch.object(self.install,'default_destination',return_value=self.destination),patch('sys.stdout',new_callable=io.StringIO) as output:
            self.install.main()
        receipt=output.getvalue()
        self.assertIn('0.2.0-beta.1',receipt);self.assertIn(str(self.destination),receipt)
        entry='WUPHF.exe' if sys.platform=='win32' else 'Start WUPHF.command' if sys.platform=='darwin' else 'Start WUPHF.sh'
        self.assertIn(str(self.destination/entry),receipt)
        self.assertIn('not configured or connected',receipt)
        self.assertNotIn('http',receipt)
