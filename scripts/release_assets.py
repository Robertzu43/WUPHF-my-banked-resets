"""Create unsigned versioned packages and verify a three-platform release set."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parent.parent
VERSION_PATTERN=r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)-(alpha|beta|rc)\.([1-9][0-9]*)'


def validate_version(version):
    if not re.fullmatch(VERSION_PATTERN,version):raise ValueError('Expected a prerelease version such as 0.1.0-beta.1.')
    return version


def validate_commit(commit):
    if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('Expected a full lowercase 40-character commit SHA.')
    return commit


def validate_checkout(version,commit):
    validate_version(version);validate_commit(commit)
    if (ROOT/'VERSION').read_text(encoding='utf-8').strip()!=version:raise ValueError('VERSION differs from requested release.')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=commit:raise ValueError('Checkout differs from requested release commit.')


def archive_name(manifest):
    version=validate_version(manifest['version'])
    operating_system=manifest['os'].lower()
    if operating_system not in ('linux','macos','windows'):raise ValueError('Unsupported release platform.')
    architecture=manifest['architecture'].lower()
    architecture={'amd64':'x86_64','aarch64':'arm64'}.get(architecture,architecture)
    if not re.fullmatch(r'[a-z0-9_]+',architecture):raise ValueError('Unsafe architecture name.')
    if manifest.get('unsigned') is not True:raise ValueError('Unsigned status must be explicit.')
    validate_commit(manifest['commit'])
    extension='zip' if operating_system=='windows' else 'tar.gz'
    return f'wuphf-{version}-{operating_system}-{architecture}-unsigned.{extension}'


def checksum(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write_checksums(paths,destination):
    paths=sorted(paths,key=lambda p:p.name)
    if len({p.name for p in paths})!=len(paths):raise ValueError('Duplicate asset filenames.')
    destination.write_text(''.join(f'{checksum(path)}  {path.name}\n' for path in paths),encoding='utf-8')


def archive_package(package,output):
    manifest=json.loads((package/'build-info.json').read_text(encoding='utf-8'))
    name=archive_name(manifest)
    paths=list(package.rglob('*'))
    for path in paths:
        if path.is_symlink() and not path.resolve().is_relative_to(package.resolve()):raise ValueError('Package symlink escapes package.')
    output.mkdir(parents=True,exist_ok=True)
    target=output/name
    if target.exists():raise ValueError('Archive already exists.')
    if name.endswith('.zip'):
        if any(path.is_symlink() for path in paths):raise ValueError('Windows ZIP cannot preserve package symlinks.')
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in paths:archive.write(path,Path('WUPHF')/path.relative_to(package))
    else:
        with tarfile.open(target,'x:gz',dereference=False) as archive:archive.add(package,arcname='WUPHF')
    write_checksums([target],output/'SHA256SUMS')
    return target


def read_manifest(archive):
    if archive.name.endswith('.zip'):
        with zipfile.ZipFile(archive) as bundle:return json.loads(bundle.read('WUPHF/build-info.json'))
    with tarfile.open(archive,'r:gz') as bundle:
        member=bundle.getmember('WUPHF/build-info.json')
        if not member.isfile():raise ValueError('Manifest must be a regular file.')
        return json.load(bundle.extractfile(member))


def assemble(source,output,version,commit):
    validate_version(version);validate_commit(commit)
    archives=sorted([*source.rglob('*.tar.gz'),*source.rglob('*.zip')])
    if len(archives)!=3:raise ValueError('Expected exactly three platform archives.')
    platforms=set();names=set()
    for archive in archives:
        manifest=read_manifest(archive)
        if manifest['version']!=version or manifest['commit']!=commit:raise ValueError('Archive version/commit mismatch.')
        if archive.name!=archive_name(manifest) or archive.name in names:raise ValueError('Archive filename mismatch or duplicate.')
        if manifest['os'] in platforms:raise ValueError('Duplicate release platform.')
        expected=f'{checksum(archive)}  {archive.name}\n'
        if (archive.parent/'SHA256SUMS').read_text(encoding='utf-8')!=expected:raise ValueError('Archive checksum mismatch.')
        platforms.add(manifest['os']);names.add(archive.name)
    if platforms!={'linux','macos','windows'}:raise ValueError('Missing release platform.')
    output.mkdir(parents=True,exist_ok=False)
    for archive in archives:shutil.copy2(archive,output/archive.name)
    write_checksums(list(output.iterdir()),output/'SHA256SUMS')


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    validate=commands.add_parser('validate');validate.add_argument('--version',required=True);validate.add_argument('--commit',required=True)
    archive=commands.add_parser('archive');archive.add_argument('package',type=Path);archive.add_argument('--output',required=True,type=Path)
    release=commands.add_parser('assemble');release.add_argument('source',type=Path);release.add_argument('--output',required=True,type=Path)
    release.add_argument('--version',required=True);release.add_argument('--commit',required=True)
    args=parser.parse_args()
    if args.command=='validate':validate_checkout(args.version,args.commit)
    elif args.command=='archive':print(archive_package(args.package,args.output))
    else:assemble(args.source,args.output,args.version,args.commit)


if __name__=='__main__':main()
