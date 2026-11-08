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
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch('scripts.build_package.subprocess.run') as run,patch('scripts.build_package.collect_notices') as notices:
                run.side_effect=lambda *args,**kwargs:(root/'dist'/'WUPHF').mkdir(parents=True)
                build_package.main()
                notices.assert_called_once_with((root/'dist'/'WUPHF'/'third-party-notices').resolve())
            import json, platform
            manifest=json.loads((root/'dist'/'WUPHF'/'build-info.json').read_text())
            self.assertEqual(manifest['architecture'],platform.machine())
            self.assertEqual(manifest['python'],platform.python_version())
        command=run.call_args_list[0].args[0]
        sources=[command[index+1].rsplit(':',1)[0] for index,value in enumerate(command) if value=='--add-data']
        self.assertTrue(all(Path(path).is_file() for path in sources))
        self.assertFalse(any(Path(path).name=='google-client.json' for path in sources))
        self.assertIn('geist-pixel-square.woff2',[Path(path).name for path in sources])
        self.assertTrue({'VERSION','README.md','CHANGELOG.md','LICENSE'}.issubset({Path(path).name for path in sources}))

    def test_smoke_refuses_local_oauth_client_before_running_artifact(self):
        from scripts import smoke_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'google-client.json').write_text('not-a-real-credential')
            with patch.object(sys,'argv',['smoke_package',str(root)]),patch('scripts.smoke_package.subprocess.run') as run:
                with self.assertRaises(SystemExit):smoke_package.main()
                run.assert_not_called()
