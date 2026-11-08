import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(os.name!='nt', 'source shell launchers require POSIX')
class SourceLauncherTests(unittest.TestCase):
    launchers=('Start WUPHF.command','Start WUPHF.sh')

    def make_source(self, root, name):
        source=root/'source folder $cash; apostrophe\' "quote" %percent';source.mkdir()
        launcher=source/name
        text=Path(name).read_text().replace('export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"','export PATH="$PATH"')
        launcher.write_text(text);launcher.chmod(0o755)
        commands=root/'commands';commands.mkdir()
        for command in ('dirname','mkdir','cp'):
            (commands/command).symlink_to(shutil.which(command))
        self.executable(commands/'codex','#!/bin/sh\nexit 0\n')
        (source/'requirements.txt').write_text('')
        return source,commands

    def executable(self, path, text):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);path.chmod(0o755)

    def interpreter(self, path, supported=True):
        self.executable(path, '#!/bin/sh\n'
            'if [ "$1" = "-c" ]; then\n'
            '  case "$2" in *keyring*) [ "${FAIL_PIP:-}" != 1 ]; exit $?;; esac\n'
            '  exit '+('0' if supported else '1')+'\nfi\n'
            'if [ "$1 $2" = "-m venv" ]; then\n'
            '  [ "${FAIL_VENV:-}" != 1 ] || exit 1\n'
            '  mkdir -p "$3/bin" && cp "$0" "$3/bin/python" || exit 1\n'
            '  printf "%s\\n" "$PWD" > created-at\n'
            'elif [ "$1 $2" = "-m pip" ]; then\n'
            '  exit 1\n'
            'elif [ "$1 $2" = "-m wuphf.web" ]; then\n'
            '  printf "WUPHF_STARTED %s\\n" "$0"\n'
            'else exit 90; fi\n')

    def run_launcher(self, source, commands, name, **environment):
        env={**os.environ,'PATH':str(commands),'WUPHF_PYTHON':''}
        env.update(environment)
        return subprocess.run(['/bin/bash' if name.endswith('.command') else '/bin/sh',str(source/name)],
                              cwd=commands,input='\n',text=True,capture_output=True,env=env,timeout=5)

    def test_old_default_uses_installed_modern_python(self):
        for name in self.launchers:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp),name)
                self.interpreter(commands/'python3',False);self.interpreter(commands/'python3.13')
                result=self.run_launcher(source,commands,name)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('WUPHF_STARTED',result.stdout)
                if name.endswith('.sh'):
                    self.assertEqual((source/'created-at').read_text().strip(),str(source))

    def test_explicit_runtime_path_with_spaces_is_used(self):
        for name in self.launchers:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source,commands=self.make_source(root,name)
                runtime=root/'Python with spaces'/'python';self.interpreter(runtime)
                result=self.run_launcher(source,commands,name,WUPHF_PYTHON=str(runtime))
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('WUPHF_STARTED',result.stdout)

    def test_invalid_override_does_not_fall_back_to_modern_python(self):
        for name in self.launchers:
            for invalid in ('old','missing'):
                with self.subTest(name=name,invalid=invalid),tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp);source,commands=self.make_source(root,name)
                    self.interpreter(commands/'python3')
                    if invalid=='old':self.interpreter(root/invalid,False)
                    result=self.run_launcher(source,commands,name,WUPHF_PYTHON=str(root/invalid))
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('WUPHF_PYTHON',result.stdout+result.stderr)
                    self.assertNotIn('WUPHF_STARTED',result.stdout)
                    self.assertFalse((source/'.venv').exists())

    def test_only_old_or_missing_python_gives_supported_runtime_recovery(self):
        for name in self.launchers:
            for old in (True,False):
                with self.subTest(name=name,old=old),tempfile.TemporaryDirectory() as tmp:
                    source,commands=self.make_source(Path(tmp),name)
                    if old:self.interpreter(commands/'python3',False)
                    result=self.run_launcher(source,commands,name)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('3.11',result.stdout+result.stderr)
                    self.assertNotIn('WUPHF_STARTED',result.stdout)
                    self.assertFalse((source/'.venv').exists())

    def test_existing_old_or_broken_environment_is_preserved(self):
        for name in self.launchers:
            for broken in (True,False):
                with self.subTest(name=name,broken=broken),tempfile.TemporaryDirectory() as tmp:
                    source,commands=self.make_source(Path(tmp),name)
                    self.interpreter(commands/'python3')
                    marker=source/'.venv'/'user-file';marker.parent.mkdir();marker.write_text('keep me')
                    if not broken:self.interpreter(source/'.venv/bin/python',False)
                    result=self.run_launcher(source,commands,name)
                    self.assertNotEqual(result.returncode,0)
                    self.assertNotIn('WUPHF_STARTED',result.stdout)
                    self.assertIn('rename',result.stdout+result.stderr)
                    self.assertEqual(marker.read_text(),'keep me')
                    self.assertFalse((source/'created-at').exists())

    def test_existing_working_environment_needs_no_global_python(self):
        for name in self.launchers:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp),name)
                self.interpreter(source/'.venv/bin/python')
                result=self.run_launcher(source,commands,name)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('.venv/bin/python',result.stdout)
                self.assertFalse((source/'created-at').exists())

    def test_linux_venv_and_pip_failures_are_actionable(self):
        for failure in ('FAIL_VENV','FAIL_PIP'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                name='Start WUPHF.sh';source,commands=self.make_source(Path(tmp),name)
                self.interpreter(commands/'python3')
                result=self.run_launcher(source,commands,name,**{failure:'1'})
                self.assertNotEqual(result.returncode,0)
                self.assertIn('README.md',result.stdout+result.stderr)
                self.assertIn('venv' if failure=='FAIL_VENV' else 'pip',result.stdout+result.stderr)
                self.assertNotIn('WUPHF_STARTED',result.stdout)


@unittest.skipUnless(os.name=='nt', 'Windows source launcher requires native cmd.exe')
class WindowsSourceLauncherTests(unittest.TestCase):
    def make_source(self, root):
        from pip._vendor.distlib.scripts import ScriptMaker
        source=root/'source folder $cash; apostrophe\' %percent !bang';source.mkdir()
        shutil.copyfile('Start WUPHF.bat',source/'Start WUPHF.bat')
        commands=root/'commands';commands.mkdir()
        (commands/'codex.cmd').write_text('@exit /b 0\n')
        (source/'requirements.txt').write_text('')
        (root/'fake_python.py').write_text("""import os, pathlib, shutil, sys

def main():
    args=sys.argv[1:]
    executable=pathlib.Path(sys.argv[0])
    if executable.suffix!='.exe': executable=pathlib.Path(str(executable)+'.exe')
    name=executable.stem
    selector=args.pop(0) if args and args[0].startswith('-3') else ''
    if args[:1]==['-c']:
        if 'keyring' in args[1]: return int(os.environ.get('FAIL_PIP','0'))
        if '.venv' in executable.parts: return int(os.environ.get('OLD_VENV','0'))
        return int(name in os.environ.get('OLD_PYTHONS','').split(',') and selector!='-3.13')
    if args[:2]==['-m','venv']:
        if os.environ.get('FAIL_VENV'): return 1
        target=pathlib.Path(args[2])/'Scripts'/'python.exe'
        target.parent.mkdir(parents=True)
        shutil.copyfile(executable,target)
        pathlib.Path('created-at').write_text(os.getcwd())
        return 0
    if args[:2]==['-m','pip']: return 1
    if args[:2]==['-m','wuphf.web']:
        print('WUPHF_STARTED '+sys.argv[0])
        return 0
    return 90
""")
        maker=ScriptMaker(None,str(commands));maker.executable=sys.executable;maker.variants={''}
        self.maker=maker
        return source,commands

    def interpreter(self, commands, name):
        self.maker.target_dir=str(commands)
        self.maker.make(name+' = fake_python:main')

    def run_launcher(self, source, commands, **environment):
        env={**os.environ,'PATH':str(commands)+';'+os.path.join(os.environ['SystemRoot'],'System32'),
             'WUPHF_PYTHON':'','PYTHONPATH':str(source.parent)}
        env.update(environment)
        return subprocess.run([os.environ.get('COMSPEC','cmd.exe'),'/d','/c',str(source/'Start WUPHF.bat')],
                              cwd=commands,input='\n',text=True,capture_output=True,env=env,timeout=15)

    def test_old_default_uses_modern_versioned_command_or_py_selector(self):
        for modern in ('python3.13','py'):
            with self.subTest(modern=modern),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp))
                self.interpreter(commands,'python');self.interpreter(commands,modern)
                result=self.run_launcher(source,commands,OLD_PYTHONS='python,py')
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('WUPHF_STARTED',result.stdout)
                self.assertEqual((source/'created-at').read_text(),str(source))

    def test_explicit_runtime_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,commands=self.make_source(Path(tmp))
            runtime=Path(tmp)/'Python with spaces';runtime.mkdir();self.interpreter(runtime,'python')
            result=self.run_launcher(source,commands,WUPHF_PYTHON=str(runtime/'python.exe'))
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('WUPHF_STARTED',result.stdout)

    def test_invalid_override_is_not_replaced_by_an_available_python(self):
        for invalid in ('old','missing'):
            with self.subTest(invalid=invalid),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp));self.interpreter(commands,'python')
                if invalid=='old':self.interpreter(commands,'old')
                result=self.run_launcher(source,commands,WUPHF_PYTHON=str(commands/(invalid+'.exe')),OLD_PYTHONS='old')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('WUPHF_PYTHON',result.stdout)
                self.assertNotIn('WUPHF_STARTED',result.stdout)
                self.assertFalse((source/'.venv').exists())

    def test_only_old_or_missing_python_reports_recovery(self):
        for old in (True,False):
            with self.subTest(old=old),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp))
                if old:self.interpreter(commands,'python')
                result=self.run_launcher(source,commands,OLD_PYTHONS='python')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('3.11',result.stdout)
                self.assertNotIn('WUPHF_STARTED',result.stdout)
                self.assertFalse((source/'.venv').exists())

    def test_existing_old_or_broken_environment_is_preserved(self):
        for broken in (True,False):
            with self.subTest(broken=broken),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp));self.interpreter(commands,'python3.13')
                marker=source/'.venv'/'user-file';marker.parent.mkdir();marker.write_text('keep me')
                if not broken:
                    runtime=source/'.venv'/'Scripts';runtime.mkdir();self.interpreter(runtime,'python')
                result=self.run_launcher(source,commands,OLD_VENV='1')
                self.assertNotEqual(result.returncode,0)
                self.assertIn('rename',result.stdout)
                self.assertNotIn('WUPHF_STARTED',result.stdout)
                self.assertEqual(marker.read_text(),'keep me')
                self.assertFalse((source/'created-at').exists())

    def test_working_environment_is_reused_without_global_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,commands=self.make_source(Path(tmp))
            runtime=source/'.venv'/'Scripts';runtime.mkdir(parents=True);self.interpreter(runtime,'python')
            result=self.run_launcher(source,commands)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('WUPHF_STARTED',result.stdout)
            self.assertFalse((source/'created-at').exists())

    def test_venv_and_pip_failures_report_recovery(self):
        for failure in ('FAIL_VENV','FAIL_PIP'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                source,commands=self.make_source(Path(tmp));self.interpreter(commands,'python')
                result=self.run_launcher(source,commands,**{failure:'1'})
                self.assertNotEqual(result.returncode,0)
                self.assertIn('README.md',result.stdout)
                self.assertIn('venv' if failure=='FAIL_VENV' else 'pip',result.stdout)
                self.assertNotIn('WUPHF_STARTED',result.stdout)


@unittest.skipUnless(os.name!='nt', 'packaged shell launcher requires POSIX')
class PackagedLauncherTests(unittest.TestCase):
    def make_package(self, root, platform):
        from scripts import build_package
        package=root/'WUPHF folder $cash; apostrophe\' "quote" %percent'
        package.mkdir();(package/'_internal').mkdir()
        executable=package/'WUPHF'
        executable.write_text('#!/bin/sh\n[ "$PWD" = "$(dirname "$0")" ] || exit 41\nprintf "%s\\n" "$@"\n')
        executable.chmod(0o755)
        with patch('scripts.build_package.sys.platform',platform):build_package.copy_package_files(package)
        return package

    def test_packaged_launchers_follow_relocation_preserve_arguments_and_repeat(self):
        for platform,name in [('darwin','Start WUPHF.command'),('linux','Start WUPHF.sh')]:
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);package=self.make_package(root,platform)
                destination=root/'new location';destination.mkdir()
                package=package.rename(destination/package.name)
                launcher=package/name
                self.assertTrue(os.access(launcher,os.X_OK))
                for _ in range(2):
                    result=subprocess.run([str(launcher),'--check-assets','a b;$HOME'],cwd=root,text=True,capture_output=True,timeout=5)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(result.stdout,'--check-assets\na b;$HOME\n')

    def test_missing_bundle_members_fail_with_recovery_instructions(self):
        for missing in ['WUPHF','_internal']:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                package=self.make_package(Path(tmp),'darwin')
                member=package/missing
                member.rmdir() if member.is_dir() else member.unlink()
                result=subprocess.run([str(package/'Start WUPHF.command')],text=True,capture_output=True,timeout=5)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('whole WUPHF folder',result.stderr)
                self.assertIn('Extract',result.stderr)

    def test_nonexecutable_binary_reports_extract_and_permission_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=self.make_package(Path(tmp),'linux');(package/'WUPHF').chmod(0o644)
            result=subprocess.run([str(package/'Start WUPHF.sh')],text=True,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('executable',result.stderr)
            self.assertIn('tar',result.stderr)
