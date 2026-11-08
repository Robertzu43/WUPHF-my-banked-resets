"""Copy third-party notices from the Python build environment, not a binary audit."""
import ast
import hashlib
import importlib.metadata as metadata
import io
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import urllib.request


NATIVE_DOCS=Path('/usr/share/doc')
HOMEBREW_CELLARS=(Path('/opt/homebrew/Cellar'),Path('/usr/local/Cellar'))


def python_source_notices(copies):
    version=platform.python_version()
    if not re.fullmatch(r'3\.[0-9]+\.[0-9]+',version):raise RuntimeError('Release notices require a final CPython version.')
    release=tuple(map(int,version.split('.')))
    url=f'https://github.com/python/cpython/archive/refs/tags/v{version}.tar.gz'
    try:
        # Read selected notice text only; never extract or execute downloaded source.
        with urllib.request.urlopen(url,timeout=30) as response:
            if not response.geturl().startswith(('https://github.com/python/cpython/','https://codeload.github.com/python/cpython/')):
                raise ValueError('Source redirect is not official CPython HTTPS.')
            body=response.read(64*1024*1024+1)
        if len(body)>64*1024*1024:raise ValueError('CPython source archive exceeds size limit.')
        prefix=f'cpython-{version}/';notices={};hacl=[]
        with tarfile.open(fileobj=io.BytesIO(body),mode='r:gz') as source:
            for member in source.getmembers():
                if not member.isfile() or not member.name.startswith(prefix):continue
                relative=member.name[len(prefix):];path=Path(relative)
                if '..' in path.parts:raise ValueError('Unsafe source notice path.')
                if (relative=='Doc/license.rst' or relative.startswith('Modules/') and
                        re.fullmatch(r'(LICENSE|COPYING|COPYRIGHT)(?:\.txt)?',path.name,re.I)):
                    if member.size>1024*1024:raise ValueError('Source notice exceeds size limit.')
                    notice=source.extractfile(member).read();notice.decode('utf-8')
                    if not notice.strip() or b'\0' in notice:raise ValueError('Empty or binary source notice.')
                    notices['python/source/'+relative]=notice
                elif relative.startswith('Modules/_hacl/') and path.suffix in ('.c','.h'):
                    header=source.extractfile(member).read(8192).decode('utf-8')
                    match=re.match(r'\s*(/\*.*?\*/)',header,re.S)
                    if match and 'Copyright' in match[1] and match[1] not in hacl:hacl.append(match[1])
        if b'Licenses and Acknowledgements for Incorporated Software' not in notices.get('python/source/Doc/license.rst',b''):
            raise ValueError('CPython incorporated-software notices missing.')
        if release[:2]==(3,11) and 'python/source/Modules/_sha3/LICENSE' not in notices:
            raise ValueError('CPython SHA3 notice missing.')
        if release[:2]>=(3,12):
            if not any('MIT License' in block for block in hacl):raise ValueError('CPython HACL notices missing.')
            notices['python/source/HACL-NOTICES.txt']=('\n\n'.join(hacl)+'\n').encode('utf-8')
    except Exception as error:
        raise RuntimeError(f'Cannot collect required CPython {version} source notices from {url}: {error}') from error
    copies.update(notices)
    return {'url':url,'sha256':hashlib.sha256(body).hexdigest(),'notices':sorted(notices)}


def native_notices(package,copies,sources=None,python_notices=(),bootloader_notices=()):
    inventory=[]
    sources=sources or {};stdlib=Path(sysconfig.get_path('stdlib')).resolve();base=Path(sys.base_prefix).resolve()
    for binary in sorted(Path(package).rglob('*')):
        if not binary.is_file():continue
        with binary.open('rb') as stream:magic=stream.read(4)
        if not (magic.startswith((b'\x7fELF',b'MZ')) or magic in (b'\xfe\xed\xfa\xce',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xcf\xfa\xed\xfe',b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca')):continue
        entry={'binary':binary.relative_to(package).as_posix(),'notices':[]}
        if binary.is_symlink():entry['alias_of']=binary.resolve().relative_to(Path(package).resolve()).as_posix()
        original=sources.get(binary.resolve())
        if original:
            source,kind=original;entry['build_source']=str(source)
            if kind=='EXECUTABLE' and binary.parent==Path(package):entry['notices'].extend(bootloader_notices)
            elif (source.is_relative_to(stdlib/'lib-dynload') or
                  source.is_relative_to(base/'DLLs') and source.suffix=='.pyd' or
                  source.is_relative_to(base) and re.fullmatch(r'(?:lib)?python(?:3[.0-9]*)?(?:\.dll|\.dylib|\.so(?:\.[0-9]+)*)?',source.name,re.I)):
                entry['notices'].extend(python_notices)
            elif sys.platform=='win32' and source.is_relative_to(base) and source.name.lower().startswith(('libcrypto','libssl','libffi','vcruntime')) and 'python/distribution-LICENSE.txt' in copies:
                entry['notices'].append('python/distribution-LICENSE.txt')
            if sys.platform=='darwin' and not entry['notices']:
                for cellar in HOMEBREW_CELLARS:
                    cellar=cellar.resolve()
                    if not source.is_relative_to(cellar):continue
                    parts=source.relative_to(cellar).parts
                    if len(parts)<3:continue
                    formula=cellar/parts[0]/parts[1]
                    for notice in sorted(formula.iterdir()):
                        if not notice.is_file() or not re.fullmatch(r'(?:LICENSE|LICENCE|COPYING|COPYRIGHT|NOTICE)(?:[._-][A-Za-z0-9._-]+)?',notice.name,re.I):continue
                        body=notice.read_bytes()
                        try:body.decode('utf-8-sig')
                        except UnicodeDecodeError:continue
                        if not body.strip() or b'\0' in body:continue
                        target=(Path('native/homebrew')/parts[0]/parts[1]/notice.name).as_posix()
                        copies[target]=body;entry['notices'].append(target)
                    entry['packages']=[f'Homebrew {parts[0]} {parts[1]}']
        # shortcut: Debian matching uses bytes; transformed non-Homebrew libraries remain explicit below.
        if sys.platform=='linux' and shutil.which('dpkg-query'):
            result=subprocess.run(['dpkg-query','--search','*/'+binary.name],capture_output=True,text=True,check=False)
            for line in result.stdout.splitlines():
                if ': ' not in line:continue
                owner,source=line.split(': ',1);source=Path(source)
                if not source.is_file():continue
                with source.open('rb') as stream:source_hash=hashlib.file_digest(stream,'sha256').digest()
                with binary.open('rb') as stream:binary_hash=hashlib.file_digest(stream,'sha256').digest()
                if source_hash!=binary_hash:continue
                for name in owner.split(', '):
                    copyright=NATIVE_DOCS/name.split(':',1)[0]/'copyright'
                    if not copyright.is_file():continue
                    details=subprocess.run(['dpkg-query','--show','--showformat=${binary:Package} ${Version}',name],capture_output=True,text=True,check=False)
                    target='native/'+re.sub(r'[^A-Za-z0-9._-]','_',name)+'/copyright'
                    copies[target]=copyright.read_bytes();entry['notices'].append(target)
                    entry.setdefault('packages',[]).append(details.stdout.strip() or name)
        if not entry['notices']:entry['reason']='No notice source identified from build provenance or installed Debian metadata. Manual review required.'
        inventory.append(entry)
    return inventory


def collect_notices(destination,package=None,collect_toc=None):
    destination=Path(destination)
    python_license=next((p for p in (Path(sysconfig.get_path('stdlib'))/'LICENSE.txt',
                                    Path(sys.base_prefix)/'LICENSE.txt') if p.is_file()),None)
    if python_license is None:raise RuntimeError('Python runtime LICENSE.txt is missing.')
    copies={'python/LICENSE.txt':python_license.read_bytes()};inventory=[]
    distribution_license=Path(sys.base_prefix)/'LICENSE.txt'
    if distribution_license.is_file():copies['python/distribution-LICENSE.txt']=distribution_license.read_bytes()
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
    python_sources=python_source_notices(copies)
    sources={}
    if collect_toc is not None:
        # PyInstaller's local build record retains originals before Mach-O relocation/signing.
        for name,original,kind in ast.literal_eval(Path(collect_toc).read_text(encoding='utf-8'))[0]:
            if kind not in ('BINARY','EXTENSION','EXECUTABLE'):continue
            target=Path(package)/(name if kind=='EXECUTABLE' else '_internal/'+name)
            if not target.resolve().is_relative_to(Path(package).resolve()):raise ValueError('Build record path escapes package.')
            sources[target.resolve()]=(Path(original).resolve(),kind)
    python_notices=[name for name in copies if name.startswith('python/')]
    bootloader_notices=next(d['notices'] for d in inventory if d['name'].lower()=='pyinstaller')
    native=native_notices(package,copies,sources,python_notices,bootloader_notices) if package is not None else []
    index={'scope':'Inventory of all installed distributions in the build environment; some may not be bundled.',
           'limitations':'This is not an exhaustive native binary license audit. OS-specific libraries may need additional notices and manual review.',
           'native_scope':'ELF, PE and Mach-O inventory. Runtime/bootloader and Homebrew notices use original paths from the local PyInstaller build record; Debian copyright requires matching bytes. Collected notices are not certification of component coverage.',
           'python':{'version':platform.python_version(),'notice':'python/LICENSE.txt','notices':python_notices,'source':python_sources},
           'native_binaries':native,'uncollected_native_binaries':[b['binary'] for b in native if not b['notices']],
           'distributions':inventory,'missing_notices':[d['name'] for d in inventory if not d['notices']]}
    destination.mkdir(parents=True,exist_ok=False)
    for relative,body in copies.items():
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    (destination/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    return index
