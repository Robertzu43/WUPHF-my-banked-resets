"""Install an already verified frozen bundle without accounts, data or scheduler changes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


PUBLIC_FILES=('LICENSE','VERSION','README.md','CHANGELOG.md','docs/user-guide.md',
              'docs/google-production.md','docs/release-readiness.md','docs/releasing.md',
              'docs/images/setup-example.jpg')
PRIVATE_FILES={'google-client.json','settings.json','state.json','gmail.json','google.json',
               'google-events.json','auth.json','.env','.env.local','credentials.json','client_secret.json'}
UPGRADE='Upgrade requires a separate procedure: disable the old background job through WUPHF, close the old setup app, and retain the old installation before choosing a new install. No files or jobs were changed.'


def default_destination():
    home=Path.home().resolve(strict=True)
    if sys.platform=='darwin':return home/'Library'/'Application Support'/'WUPHF'
    if sys.platform=='linux':return home/'.local'/'opt'/'WUPHF'
    if sys.platform=='win32':
        local=os.environ.get('LOCALAPPDATA','')
        path=Path(local)
        if not local or not path.is_absolute() or not path.is_relative_to(home) or '..' in path.parts:
            raise ValueError('LOCALAPPDATA must be an absolute directory inside your user home.')
        return path/'WUPHF'
    raise ValueError('Local installation is unsupported on this platform.')


def launch_entry(package):
    name={'darwin':'Start WUPHF.command','linux':'Start WUPHF.sh','win32':'WUPHF.exe'}.get(sys.platform)
    if name is None:raise ValueError('Local installation is unsupported on this platform.')
    return package/name


def _safe_parent(destination):
    home=Path.home().resolve(strict=True)
    if not destination.is_absolute() or not destination.is_relative_to(home) or destination==home or '..' in destination.parts:
        raise ValueError('Installation destination must be inside your user home.')
    if any(ord(char)<32 or ord(char)==127 for char in str(destination)):
        raise ValueError('Unsupported control character in installation path.')
    parents=[home]
    for part in destination.relative_to(home).parts[:-1]:parents.append(parents[-1]/part)
    for parent in parents:
        try:info=parent.lstat()
        except FileNotFoundError:continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0):
            raise ValueError('Installation parent must not be a link or junction.')
        if not stat.S_ISDIR(info.st_mode):raise ValueError('Installation parent is not a directory.')
        if os.name!='nt' and (info.st_uid!=os.getuid() or info.st_mode&0o022):
            raise ValueError('Installation parent must be user owned and not writable by other users.')


def _inventory(root):
    if root.is_symlink() or not root.is_dir():raise ValueError('Incomplete bundle: expected a real package directory.')
    entries={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in sorted(dirs+files):
            path=Path(directory)/name;info=path.lstat()
            if name.casefold() in PRIVATE_FILES:raise ValueError('User configuration found in bundle; install only a clean release.')
            if any(ord(char)<32 or ord(char)==127 for char in name):raise ValueError('Unsupported control character in bundle path.')
            kind=stat.S_IFMT(info.st_mode)
            if getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0) and kind!=stat.S_IFLNK:
                raise ValueError('Unsupported link or junction in bundle.')
            if kind not in (stat.S_IFREG,stat.S_IFDIR,stat.S_IFLNK):raise ValueError('Unsupported special file in bundle.')
            value=None
            if kind==stat.S_IFLNK:
                value=os.readlink(path)
                try:
                    if (os.path.isabs(value) or not Path(os.path.normpath(path.parent/value)).is_relative_to(root)
                            or not path.resolve(strict=True).is_relative_to(root)):
                        raise ValueError('Bundle link escapes the package.')
                except (OSError,RuntimeError):raise ValueError('Bundle link is broken or cyclic.') from None
            entries[path.relative_to(root).as_posix()]=(kind,stat.S_IMODE(info.st_mode),value)
    return entries


def _validate_bundle(root):
    entries=_inventory(root)
    executable=root/('WUPHF.exe' if sys.platform=='win32' else 'WUPHF')
    entry=launch_entry(root)
    required=[executable,entry,root/'build-info.json',root/'third-party-notices'/'index.json',
              root/'third-party-notices'/'python'/'LICENSE.txt',
              *(root/relative for relative in PUBLIC_FILES),
              *(root/'_internal'/relative for relative in PUBLIC_FILES),
              *(root/'_internal'/'wuphf'/relative for relative in ('web.html','translations.json','oauth-client.json',
                  'assets/geist-pixel-square.woff2','assets/geist-pixel-OFL.txt'))]
    if not (root/'_internal').is_dir() or any(not path.is_file() for path in required):
        raise ValueError('Incomplete bundle. Extract the complete original WUPHF folder, including _internal, docs and third-party-notices.')
    if os.name!='nt' and (not os.access(executable,os.X_OK) or not os.access(entry,os.X_OK)):
        raise ValueError('Incomplete executable permissions; extract the original tar.gz with tar.')
    for relative in PUBLIC_FILES:
        if (root/relative).read_bytes()!=(root/'_internal'/relative).read_bytes():
            raise ValueError('Bundle help copies differ; use a complete original release.')
    version=(root/'VERSION').read_text(encoding='utf-8').strip()
    try:
        metadata=json.loads((root/'build-info.json').read_text(encoding='utf-8'))
        if (not version or any(ord(char)<32 or ord(char)==127 for char in version)
                or not isinstance(metadata,dict) or metadata.get('version')!=version
                or metadata.get('os')!={'darwin':'macos','linux':'linux','win32':'windows'}[sys.platform]):
            raise ValueError('Bundle version or platform metadata is inconsistent.')
        notices=json.loads((root/'third-party-notices'/'index.json').read_text(encoding='utf-8'))
        if not isinstance(notices,dict) or notices.get('python',{}).get('notice')!='python/LICENSE.txt':
            raise ValueError('Bundle third-party notices are incomplete.')
        client=json.loads((root/'_internal'/'wuphf'/'oauth-client.json').read_text(encoding='utf-8'))
        if (not isinstance(client,dict) or set(client)!={'installed'} or not isinstance(client['installed'],dict)
                or set(client['installed'])!={'client_id','client_secret'}
                or not all(isinstance(value,str) and value.strip() for value in client['installed'].values())
                or not client['installed']['client_id'].endswith('.apps.googleusercontent.com')):
            raise ValueError('Bundle public OAuth registration is invalid.')
    except (json.JSONDecodeError,AttributeError,TypeError):raise ValueError('Bundle metadata is invalid.') from None
    for relative,(kind,mode,value) in list(entries.items()):
        if kind==stat.S_IFREG:
            with (root/relative).open('rb') as stream:value=hashlib.file_digest(stream,'sha256').digest()
        entries[relative]=(kind,mode,value)
    return entries


def _copy_bundle(source,staging):
    if sys.platform!='darwin':
        shutil.copytree(source,staging,symlinks=True,dirs_exist_ok=True)
        return
    import subprocess
    # copy2 on macOS drops extended attributes, including quarantine information.
    env={key:value for key,value in os.environ.items() if not key.startswith('DITTO')}
    env['DITTOABORT']='1'
    try:
        subprocess.run(['/usr/bin/ditto','--rsrc','--extattr','--qtn',str(source),str(staging)],
                       check=True,capture_output=True,env=env)
    except (OSError,subprocess.SubprocessError):
        raise OSError('Could not copy the bundle with macOS ditto; check disk space and file permissions. No installed application was replaced.') from None


def _promote(staging,destination):
    if os.name=='nt':
        os.rename(staging,destination)
        return
    import ctypes
    library=ctypes.CDLL(None,use_errno=True)
    name={'darwin':'renamex_np','linux':'renameat2'}.get(sys.platform)
    if name is None:raise ValueError('Local installation is unsupported on this platform.')
    rename=getattr(library,name,None)
    if rename is None:raise RuntimeError('Atomic installation is unavailable on this runtime; keep the bundle intact and use manual permanent placement.')
    if sys.platform=='darwin':
        rename.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_uint]
        args=(os.fsencode(staging),os.fsencode(destination),4) # RENAME_EXCL
    else:
        rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
        args=(-100,os.fsencode(staging),-100,os.fsencode(destination),1) # AT_FDCWD, RENAME_NOREPLACE
    rename.restype=ctypes.c_int
    if rename(*args)!=0:
        error=ctypes.get_errno()
        raise OSError(error,os.strerror(error),str(destination))


def install_bundle(source,destination):
    source=Path(source).absolute();destination=Path(destination).absolute()
    if source.is_symlink():raise ValueError('Incomplete bundle: expected a real package directory, not a root link.')
    source=source.resolve(strict=True)
    resolved_source=source;resolved_destination=destination.resolve()
    if resolved_source!=resolved_destination and (resolved_source.is_relative_to(resolved_destination) or resolved_destination.is_relative_to(resolved_source)):
        raise ValueError('Source and installation destination overlap; run from the extracted download folder.')
    _safe_parent(destination)
    original=_validate_bundle(source)
    if source==destination:return destination
    if destination.exists() or destination.is_symlink():
        try:identical=_validate_bundle(destination)==original
        except ValueError:identical=False
        if identical:return destination
        raise ValueError(UPGRADE)
    destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    _safe_parent(destination)
    staging=Path(tempfile.mkdtemp(prefix='.WUPHF-install-',dir=destination.parent))
    candidate=staging/'WUPHF'
    try:
        _copy_bundle(source,candidate)
        if _validate_bundle(candidate)!=original:raise ValueError('Copied bundle differs from the source; no installation was promoted.')
        _safe_parent(destination)
        _promote(candidate,destination)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return destination


def main():
    if not getattr(sys,'frozen',False):
        raise ValueError('--install supports frozen release bundles only; source installation follows the source fallback instructions.')
    destination=install_bundle(Path(sys.executable).absolute().parent,default_destination())
    version=(destination/'VERSION').read_text(encoding='utf-8').strip()
    print(f'WUPHF {version}\nInstalled: {destination}\nReopen: {launch_entry(destination)}\nLocal bundle checked; not configured or connected. Continue setup from the installed reopen entry.')
