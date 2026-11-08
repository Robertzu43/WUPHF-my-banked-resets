"""Build an unsigned, one-folder WUPHF prototype in explicit output directories."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

if __package__:
    from .package_notices import collect_notices
else:
    from package_notices import collect_notices

ROOT=Path(__file__).resolve().parent.parent


def validate_public_client(path):
    raw=json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(raw,dict) or set(raw)!={'installed'} or not isinstance(raw['installed'],dict)
            or set(raw['installed'])!={'client_id','client_secret'}
            or not all(isinstance(value,str) and value.strip() for value in raw['installed'].values())
            or not raw['installed']['client_id'].endswith('.apps.googleusercontent.com')):
        raise ValueError('Bundled OAuth file must contain only the public Desktop client ID and client secret.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.resolve();work=args.work.resolve()
    if (output/'WUPHF').exists():raise SystemExit('Output already exists; choose an empty directory.')
    work.mkdir(parents=True,exist_ok=True)
    validate_public_client(ROOT/'wuphf'/'oauth-client.json')
    command=[sys.executable,'-m','PyInstaller','--onedir','--name','WUPHF','--specpath',str(work)]
    build_options=['--noconfirm','--distpath',str(output),'--workpath',str(work/'build')]
    for source,dest in (('wuphf/web.html','wuphf'),('wuphf/translations.json','wuphf'),
                        ('wuphf/oauth-client.json','wuphf'),
                        ('wuphf/assets/geist-pixel-square.woff2','wuphf/assets'),
                        ('wuphf/assets/geist-pixel-OFL.txt','wuphf/assets'),('LICENSE','.'),
                        ('VERSION','.'),('README.md','.'),('CHANGELOG.md','.')):
        command+=['--add-data',str(ROOT/source)+':'+dest]
    if sys.platform in ('win32','linux'):
        command+=['--collect-all','keyring','--hidden-import',
                  'keyring.backends.Windows' if sys.platform=='win32' else 'keyring.backends.SecretService']
    command.append(str(ROOT/'wuphf_launcher.py'))
    if sys.platform=='win32':
        windows=Path(os.environ['SystemRoot']);base=Path(sys.base_prefix)
        # Limit build-time DLL discovery to Python and Windows, not unrelated tools on the runner's PATH.
        env={**os.environ,'PATH':os.pathsep.join(map(str,(Path(sys.executable).parent,base,base/'DLLs',windows/'System32',windows)))}
        subprocess.run([sys.executable,'-m','PyInstaller.utils.cliutils.makespec',*command[3:]],cwd=ROOT,env=env,check=True)
        spec=work/'WUPHF.spec';body=spec.read_text(encoding='utf-8');marker='\npyz = PYZ('
        if body.count(marker)!=1:raise RuntimeError('Unexpected PyInstaller spec layout; cannot apply Windows system DLL policy.')
        # Windows 10+ always uses its OS UCRT; retain separate VC runtimes such as vcruntime140.dll.
        system_dll_filter='''
import ntpath, re
a.binaries = [entry for entry in a.binaries if not re.fullmatch(
    r'(?:ucrtbase|api-ms-win-(?:core|crt)-.+)\\.dll', ntpath.basename(entry[0]), re.IGNORECASE)]
'''
        spec.write_text(body.replace(marker,system_dll_filter+marker,1),encoding='utf-8')
        subprocess.run([sys.executable,'-m','PyInstaller',*build_options,str(spec)],cwd=ROOT,env=env,check=True)
    else:
        subprocess.run([*command,*build_options],cwd=ROOT,check=True)
    collect_notices(output/'WUPHF'/'third-party-notices',output/'WUPHF',work/'build'/'WUPHF'/'COLLECT-00.toc')
    manifest={'version':(ROOT/'VERSION').read_text(encoding='utf-8').strip(),
              'platform':platform.platform(),'architecture':platform.machine(),
              'python':platform.python_version(),
              'os':{'Darwin':'macos','Windows':'windows','Linux':'linux'}[platform.system()],
              'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'unsigned':True}
    (output/'WUPHF'/'build-info.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
