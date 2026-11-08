"""Copy third-party notices from the Python build environment, not a binary audit."""
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import sys
import sysconfig


def collect_notices(destination):
    destination=Path(destination)
    python_license=next((p for p in (Path(sysconfig.get_path('stdlib'))/'LICENSE.txt',
                                    Path(sys.base_prefix)/'LICENSE.txt') if p.is_file()),None)
    if python_license is None:raise RuntimeError('Python runtime LICENSE.txt is missing.')
    copies={'python/LICENSE.txt':python_license.read_bytes()};inventory=[]
    for dist in sorted(metadata.distributions(),key=lambda d:d.metadata['Name'].lower()):
        name=dist.metadata['Name'];version=dist.version
        label=re.sub(r'[^A-Za-z0-9._-]','_',name+'-'+version)
        notices=[]
        for file in dist.files or ():
            path=Path(file)
            if (not path.parts or not path.parts[0].endswith(('.dist-info','.egg-info'))
                    or '..' in path.parts or not re.match(r'^(license|licence|notice|copying)(?:[._-]|$)',path.name,re.I)
                    or path.suffix.lower() not in ('','.txt','.md','.rst','.text','.apache','.bsd','.mit')):continue
            source=Path(dist.locate_file(file))
            if not source.is_file():continue
            body=source.read_bytes()
            try:body.decode('utf-8-sig')
            except UnicodeDecodeError:continue
            if not body.strip() or b'\0' in body:continue
            target=(Path(label)/Path(*path.parts[1:])).as_posix()
            copies[target]=body;notices.append(target)
        inventory.append({'name':name,'version':version,'requires':list(dist.requires or ()),
                          'notices':notices})
    if not any(d['name'].lower()=='pyinstaller' and d['notices'] for d in inventory):
        raise RuntimeError('PyInstaller license/exception notice is missing.')
    index={'scope':'Inventory of all installed distributions in the build environment; some may not be bundled.',
           'limitations':'This is not an exhaustive native binary license audit. OS-specific libraries may need additional notices and manual review.',
           'python':{'version':platform.python_version(),'notice':'python/LICENSE.txt'},
           'distributions':inventory,'missing_notices':[d['name'] for d in inventory if not d['notices']]}
    destination.mkdir(parents=True,exist_ok=False)
    for relative,body in copies.items():
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    (destination/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    return index
