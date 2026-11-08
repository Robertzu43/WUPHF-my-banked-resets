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
        with tempfile.TemporaryDirectory() as tmp,patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.subprocess.run',side_effect=run),patch('sys.stdout',new_callable=io.StringIO) as output:
            with self.assertRaises(subprocess.CalledProcessError):smoke_package.main()
        self.assertIn('Synthetic child marker: synthetic marker',output.getvalue())
        self.assertIn('Synthetic child stderr: synthetic failure',output.getvalue())

    def test_build_bundles_only_explicit_asset_files(self):
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch('scripts.build_package.subprocess.run') as run,patch('scripts.build_package.collect_notices') as notices,patch('scripts.build_package.subprocess.check_output',return_value='a'*40),patch('scripts.build_package.platform.platform',return_value='test OS'):
                run.side_effect=lambda *args,**kwargs:(root/'dist'/'WUPHF').mkdir(parents=True)
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
        self.assertTrue({'VERSION','README.md','CHANGELOG.md','LICENSE'}.issubset({Path(path).name for path in sources}))

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
            with patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.tempfile.TemporaryDirectory',side_effect=RuntimeError('synthetic smoke boundary')):
                with self.assertRaisesRegex(RuntimeError,'synthetic smoke boundary'):smoke_package.main()
            path.write_text(json.dumps({'installed':{**client['installed'],'refresh_token':'user-token'}}))
            with patch.object(sys,'argv',['smoke_package',tmp]),patch('scripts.smoke_package.subprocess.run') as run:
                with self.assertRaises(ValueError):smoke_package.main()
                run.assert_not_called()
