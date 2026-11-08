import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

class PackageTests(unittest.TestCase):
    def test_build_bundles_only_explicit_asset_files(self):
        from scripts import build_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(sys,'argv',['build_package','--output',str(root/'dist'),'--work',str(root/'work')]),patch('scripts.build_package.subprocess.run') as run:
                build_package.main()
        command=run.call_args.args[0]
        sources=[command[index+1].rsplit(':',1)[0] for index,value in enumerate(command) if value=='--add-data']
        self.assertTrue(all(Path(path).is_file() for path in sources))
        self.assertFalse(any(Path(path).name=='google-client.json' for path in sources))
        self.assertIn('geist-pixel-square.woff2',[Path(path).name for path in sources])

    def test_smoke_refuses_local_oauth_client_before_running_artifact(self):
        from scripts import smoke_package
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'google-client.json').write_text('not-a-real-credential')
            with patch.object(sys,'argv',['smoke_package',str(root)]),patch('scripts.smoke_package.subprocess.run') as run:
                with self.assertRaises(SystemExit):smoke_package.main()
                run.assert_not_called()
