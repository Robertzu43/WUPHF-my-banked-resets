import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

class PackageTests(unittest.TestCase):
    def test_smoke_reports_only_synthetic_child_diagnostics_on_failure(self):
        import io, subprocess
        from scripts import smoke_package
        def run(command,**kwargs):
            if command[-1]=='--background':
                root=Path(kwargs['env']['HOME']).parent
                (root/'codex-was-run').write_text('synthetic marker')
                (root/'synthetic-child-stderr.txt').write_text('synthetic failure')
                raise subprocess.CalledProcessError(1,command)
            return subprocess.CompletedProcess(command,0,stdout='',stderr='')
        with tempfile.TemporaryDirectory() as tmp,patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.validate_package'),patch('scripts.smoke_package.subprocess.run',side_effect=run),patch('sys.stdout',new_callable=io.StringIO) as output:
            with self.assertRaises(subprocess.CalledProcessError):smoke_package.main()
        self.assertIn('Synthetic child marker: synthetic marker',output.getvalue())
        self.assertIn('Synthetic child stderr: synthetic failure',output.getvalue())

    def test_build_bundles_only_explicit_asset_files(self):
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch('scripts.build_package.subprocess.run') as run,patch('scripts.build_package.collect_notices') as notices,patch('scripts.build_package.subprocess.check_output',return_value='a'*40),patch('scripts.build_package.platform.platform',return_value='test OS'):
                def build(command,**kwargs):
                    if command[2]=='PyInstaller.utils.cliutils.makespec':(root/'work'/'WUPHF.spec').write_text('a = Analysis([])\npyz = PYZ(a.pure)\n')
                    else:(root/'dist'/'WUPHF').mkdir(parents=True)
                run.side_effect=build
                build_package.main()
                notices.assert_called_once_with((root/'dist'/'WUPHF'/'third-party-notices').resolve(),(root/'dist'/'WUPHF').resolve(),(root/'work'/'build'/'WUPHF'/'COLLECT-00.toc').resolve())
            import json, platform
            manifest=json.loads((root/'dist'/'WUPHF'/'build-info.json').read_text())
            self.assertEqual(manifest['architecture'],platform.machine())
            self.assertEqual(manifest['python'],platform.python_version())
            self.assertEqual(manifest['commit'],'a'*40)
            self.assertIs(manifest['unsigned'],True)
        command=run.call_args_list[0].args[0]
        sources=[command[index+1].rsplit(':',1)[0] for index,value in enumerate(command) if value=='--add-data']
        self.assertTrue(all(Path(path).is_file() for path in sources))
        self.assertFalse(any(Path(path).name=='google-client.json' for path in sources))
        self.assertIn('oauth-client.json',[Path(path).name for path in sources])
        self.assertIn('geist-pixel-square.woff2',[Path(path).name for path in sources])
        self.assertTrue({'VERSION','README.md','CHANGELOG.md','LICENSE','user-guide.md','google-production.md','setup-example.jpg'}.issubset({Path(path).name for path in sources}))

    def test_windows_build_uses_python_system_path_and_omits_only_os_ucrt_dlls(self):
        import os
        from types import SimpleNamespace
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'Python';windows=root/'Windows';jdk=root/'Temurin'/'bin'
            names=['ucrtbase.dll','API-MS-WIN-CRT-STDIO-L1-1-0.DLL','nested/api-ms-win-core-file-l1-1-0.dll',
                   'vcruntime140.dll','vcruntime140_1.dll','msvcp140.dll','python311.dll','libcrypto-3.dll',
                   'api-ms-win-other.dll','custom-ucrtbase.dll']
            binaries=[(name,str(jdk/name),'BINARY') for name in names];collected=[];calls=[]
            def build(command,**kwargs):
                calls.append((command,kwargs))
                if command[2]=='PyInstaller.utils.cliutils.makespec':
                    (root/'work'/'WUPHF.spec').write_text('a = Analysis([])\npyz = PYZ(a.pure)\ncoll = COLLECT(a.binaries)\n')
                else:
                    scope={'Analysis':lambda *args:SimpleNamespace(binaries=binaries,pure=[]),'PYZ':lambda *args:None,'COLLECT':collected.extend}
                    exec((root/'work'/'WUPHF.spec').read_text(),scope)
                    (root/'dist'/'WUPHF').mkdir(parents=True)
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch.object(sys,'platform','win32'),patch.object(sys,'base_prefix',str(base)),patch.object(sys,'executable',str(base/'python.exe')),patch.dict(os.environ,{'PATH':str(jdk),'SystemRoot':str(windows),'WUPHF_TEST_ENV':'retained'}),patch.object(build_package.subprocess,'run',side_effect=build),patch.object(build_package.subprocess,'check_output',return_value='a'*40),patch.object(build_package,'collect_notices'),patch.object(build_package.platform,'platform',return_value='Windows'):
                build_package.main()
                self.assertEqual(os.environ['PATH'],str(jdk))
            self.assertEqual([entry[0] for entry in collected],names[3:])
            self.assertEqual(len(calls),2)
            for command,kwargs in calls:
                self.assertEqual(kwargs['env']['PATH'].split(os.pathsep),list(map(str,(base,base,base/'DLLs',windows/'System32',windows))))
                self.assertEqual(kwargs['env']['WUPHF_TEST_ENV'],'retained');self.assertTrue(kwargs['check'])
                self.assertEqual(kwargs['cwd'],build_package.ROOT)
            self.assertIn('--collect-all',calls[0][0]);self.assertIn('keyring.backends.Windows',calls[0][0])
            self.assertIn('--add-data',calls[0][0]);self.assertIn('--onedir',calls[0][0])
            self.assertEqual(calls[1][0][-1],str((root/'work'/'WUPHF.spec').resolve()))

    def test_windows_build_refuses_unrecognized_spec_before_building_package(self):
        import os
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def make_spec(*args,**kwargs):(root/'work'/'WUPHF.spec').write_text('unexpected future spec layout\n')
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch.object(sys,'platform','win32'),patch.dict(os.environ,{'SystemRoot':str(root/'Windows')}),patch.object(build_package.subprocess,'run',side_effect=make_spec) as run,patch.object(build_package,'collect_notices') as notices:
                with self.assertRaisesRegex(RuntimeError,'Unexpected PyInstaller spec'):build_package.main()
                run.assert_called_once();notices.assert_not_called()
            self.assertFalse((root/'dist').exists())

    def test_smoke_refuses_local_oauth_client_before_running_artifact(self):
        from scripts import smoke_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'google-client.json').write_text('not-a-real-credential')
            with patch.object(sys,'argv',['smoke_package',str(root)]),patch('scripts.smoke_package.subprocess.run') as run:
                with self.assertRaises(SystemExit):smoke_package.main()
                run.assert_not_called()

    def test_public_client_whitelist_rejects_user_tokens_and_unknown_fields(self):
        import json
        from scripts.build_package import validate_public_client
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'oauth-client.json'
            client={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'public-desktop-value'}}
            path.write_text(json.dumps(client));validate_public_client(path)
            for raw in [{**client,'refresh_token':'user-token'},{'installed':{**client['installed'],'access_token':'token'}},{'installed':{'client_id':123,'client_secret':'public'}},[]]:
                path.write_text(json.dumps(raw))
                with self.assertRaises(ValueError):validate_public_client(path)

    def test_smoke_allows_only_whitelisted_public_oauth_registration(self):
        import json
        from scripts import smoke_package
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'oauth-client.json'
            client={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'public-desktop-value'}}
            path.write_text(json.dumps(client))
            with patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.validate_package'),patch('scripts.smoke_package.tempfile.TemporaryDirectory',side_effect=RuntimeError('synthetic smoke boundary')):
                with self.assertRaisesRegex(RuntimeError,'synthetic smoke boundary'):smoke_package.main()
            path.write_text(json.dumps({'installed':{**client['installed'],'refresh_token':'user-token'}}))
            with patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.subprocess.run') as run:
                with self.assertRaises(ValueError):smoke_package.main()
                run.assert_not_called()


class PackageLayoutTests(unittest.TestCase):
    def make_package(self, package):
        import os, shutil
        from scripts import build_package, smoke_package
        build_package.copy_package_files(package)
        for relative in build_package.PUBLIC_FILES:
            target=package/'_internal'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(package/relative,target)
        executable=package/('WUPHF.exe' if os.name=='nt' else 'WUPHF')
        executable.write_text('');executable.chmod(0o755)
        smoke_package.validate_package(package)

    def test_public_help_is_reachable_beside_executable_and_internal_readme(self):
        import re
        from urllib.parse import unquote, urlsplit
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)
            self.make_package(package)
            for relative in ['README.md','LICENSE','CHANGELOG.md','VERSION','docs/user-guide.md','docs/google-production.md','docs/images/setup-example.jpg']:
                self.assertEqual((package/relative).read_bytes(),(build_package.ROOT/relative).read_bytes())
            for base in [package,package/'_internal']:
                for relative in (path for path in build_package.PUBLIC_FILES if path.endswith('.md')):
                    document=base/relative
                    links=re.findall(r'\]\(([^)]+)\)|(?:href|src)="([^"]+)"',document.read_text())
                    for markdown,html in links:
                        link=urlsplit(markdown or html)
                        if link.scheme or link.netloc or not link.path:continue
                        self.assertTrue((document.parent/unquote(link.path)).is_file(),(relative,link.path))

    def test_smoke_rejects_missing_bundle_files_before_running_executable(self):
        from scripts import build_package, smoke_package
        import os, shutil
        missing_files=['WUPHF.exe' if os.name=='nt' else 'WUPHF','_internal','docs/user-guide.md','docs/images/setup-example.jpg','_internal/docs/user-guide.md']
        if sys.platform in ('darwin','linux'):missing_files.append('Start WUPHF.command' if sys.platform=='darwin' else 'Start WUPHF.sh')
        for missing in missing_files:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                package=Path(tmp);self.make_package(package)
                member=package/missing
                shutil.rmtree(member) if member.is_dir() else member.unlink()
                with patch.object(sys,'argv',['smoke_package',str(package)]),patch('scripts.smoke_package.subprocess.run') as run:
                    with self.assertRaisesRegex(SystemExit,'incomplete'):smoke_package.main()
                    run.assert_not_called()

    def test_smoke_rejects_inconsistent_help_copies(self):
        from scripts import smoke_package
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp);self.make_package(package)
            (package/'docs/user-guide.md').write_text('stale help')
            with self.assertRaisesRegex(SystemExit,'copies differ'):smoke_package.validate_package(package)
