"""Build an unsigned, one-folder WUPHF prototype in explicit output directories."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.resolve();work=args.work.resolve()
    if (output/'WUPHF').exists():raise SystemExit('Output already exists; choose an empty directory.')
    work.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--name','WUPHF',
             '--distpath',str(output),'--workpath',str(work/'build'),'--specpath',str(work)]
    for source,dest in (('wuphf/web.html','wuphf'),('wuphf/translations.json','wuphf'),
                        ('wuphf/assets/geist-pixel-square.woff2','wuphf/assets'),
                        ('wuphf/assets/geist-pixel-OFL.txt','wuphf/assets'),('LICENSE','.')):
        command+=['--add-data',str(ROOT/source)+':'+dest]
    if sys.platform in ('win32','linux'):
        command+=['--collect-all','keyring','--hidden-import',
                  'keyring.backends.Windows' if sys.platform=='win32' else 'keyring.backends.SecretService']
    command.append(str(ROOT/'wuphf_launcher.py'))
    subprocess.run(command,cwd=ROOT,check=True)


if __name__=='__main__':main()
