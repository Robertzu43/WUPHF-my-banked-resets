import ctypes
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import smoke_package


class WindowsSmokeTests(unittest.TestCase):
    def test_child_accepts_empty_directory_with_one_character_buffer_requirement(self):
        for directory in ('', 'C:\\WUPHF\\_internal'):
            def dll_directory(size, buffer):
                if size==0:return len(directory)+1
                buffer.value=directory
                return len(directory)

            def run(command, **kwargs):
                if command[-1]=='--background':
                    home=Path(kwargs['env']['HOME'])
                    script=(home.parent/'fake bin'/'fake_codex.py').read_text()
                    kernel=SimpleNamespace(GetDllDirectoryW=dll_directory)
                    with patch.object(sys,'platform','win32'),patch.object(sys,'stdin',io.StringIO('')),patch.object(ctypes,'windll',SimpleNamespace(kernel32=kernel),create=True):
                        exec(compile(script,'synthetic_codex','exec'),{})
                    state=home/'.local'/'share'/'wuphf-resets'/'state.json'
                    state.parent.mkdir(parents=True)
                    state.write_text(json.dumps({'last_check':1}))
                return subprocess.CompletedProcess(command,0,stdout='',stderr='')

            with self.subTest(directory=directory),tempfile.TemporaryDirectory() as tmp,patch.object(sys,'argv',['smoke_package',tmp]),patch.object(subprocess,'run',side_effect=run),patch.object(smoke_package,'validate_package'),patch('sys.stdout',new_callable=io.StringIO):
                if directory:
                    with self.assertRaisesRegex(AssertionError,'DLL directory'):smoke_package.main()
                else:smoke_package.main()
