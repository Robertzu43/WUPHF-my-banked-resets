import json
import os
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch
import zipfile
from scripts import release_assets as assets


class ReleaseAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.manifest={'version':'0.1.0-beta.1','os':'linux','architecture':'x86_64','commit':'a'*40,'unsigned':True}

    def package(self,operating_system):
        package=self.root/operating_system/'WUPHF';package.mkdir(parents=True)
        manifest={**self.manifest,'os':operating_system,'architecture':'AMD64' if operating_system=='windows' else 'arm64'}
        (package/'build-info.json').write_text(json.dumps(manifest))
        (package/'third-party-notices').mkdir();(package/'third-party-notices'/'index.json').write_text('{}')
        (package/'program').write_bytes(b'program');(package/'program').chmod(0o755)
        return package

    def release_set(self):
        source=self.root/'artifacts'
        for os_name in ('linux','macos','windows'):
            assets.archive_package(self.package(os_name),source/os_name)
        return source

    def test_filename_has_version_os_normalized_architecture_and_unsigned_status(self):
        self.assertEqual(assets.archive_name(self.manifest),'wuphf-0.1.0-beta.1-linux-x86_64-unsigned.tar.gz')
        self.assertEqual(assets.archive_name({**self.manifest,'os':'windows','architecture':'AMD64'}),'wuphf-0.1.0-beta.1-windows-x86_64-unsigned.zip')
        for key,value in [('version','../beta'),('version','1.0.0'),('version','01.0.0-beta.1'),('version','1.0.0-beta.0'),('architecture','../arm'),('os','unknown'),('commit','main'),('unsigned',False)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):assets.archive_name({**self.manifest,key:value})

    def test_checkout_requires_matching_version_and_immutable_commit(self):
        (self.root/'VERSION').write_text(self.manifest['version'])
        with patch.object(assets,'ROOT',self.root),patch.object(assets.subprocess,'check_output',return_value='a'*40+'\n'):
            assets.validate_checkout(self.manifest['version'],'a'*40)
            with self.assertRaises(ValueError):assets.validate_checkout('0.1.0-beta.2','a'*40)
            with self.assertRaises(ValueError):assets.validate_checkout(self.manifest['version'],'b'*40)
            with self.assertRaises(ValueError):assets.validate_checkout(self.manifest['version'],'--help')

    @unittest.skipIf(os.name=='nt','POSIX symlink and executable-mode preservation')
    def test_posix_archive_preserves_symlink_mode_and_notices(self):
        package=self.package('macos');(package/'link').symlink_to('program')
        archive=assets.archive_package(package,self.root/'out')
        with tarfile.open(archive) as bundle:
            self.assertTrue(bundle.getmember('WUPHF/link').issym())
            self.assertEqual(bundle.getmember('WUPHF/program').mode & 0o777,0o755)
            self.assertIn('WUPHF/third-party-notices/index.json',bundle.getnames())
        self.assertEqual(assets.read_manifest(archive)['os'],'macos')

    @unittest.skipIf(os.name=='nt','POSIX symlink support')
    def test_external_symlink_is_rejected(self):
        package=self.package('linux');(package/'link').symlink_to(self.root/'outside')
        with self.assertRaisesRegex(ValueError,'escapes'):assets.archive_package(package,self.root/'out')

    def test_windows_zip_contains_manifest_and_notices(self):
        archive=assets.archive_package(self.package('windows'),self.root/'out')
        with zipfile.ZipFile(archive) as bundle:
            self.assertIn('WUPHF/third-party-notices/index.json',bundle.namelist())
        self.assertEqual(assets.read_manifest(archive)['os'],'windows')

    def test_combined_checksums_match_downloadable_assets(self):
        source=self.release_set();output=self.root/'release'
        assets.assemble(source,output,self.manifest['version'],self.manifest['commit'])
        lines=(output/'SHA256SUMS').read_text().splitlines();self.assertEqual(len(lines),3)
        for line in lines:
            digest,name=line.split('  ');self.assertEqual(digest,assets.checksum(output/name))
            self.assertNotIn('/',name)

    def test_wrong_commit_corruption_and_incomplete_set_fail_before_output(self):
        source=self.release_set();output=self.root/'release'
        with self.assertRaisesRegex(ValueError,'commit'):assets.assemble(source,output,self.manifest['version'],'b'*40)
        checksum_file=source/'linux'/'SHA256SUMS';checksum_file.write_text('bad checksum')
        with self.assertRaisesRegex(ValueError,'checksum'):assets.assemble(source,output,self.manifest['version'],self.manifest['commit'])
        next((source/'windows').glob('*.zip')).unlink()
        with self.assertRaisesRegex(ValueError,'three'):assets.assemble(source,output,self.manifest['version'],self.manifest['commit'])
        self.assertFalse(output.exists())

    def test_manifest_and_download_name_must_agree(self):
        source=self.release_set();archive=next((source/'linux').glob('*.tar.gz'))
        archive.rename(archive.with_name(archive.name.replace('linux','windows')))
        with self.assertRaisesRegex(ValueError,'filename'):assets.assemble(source,self.root/'out',self.manifest['version'],self.manifest['commit'])

    def test_duplicate_platform_and_duplicate_checksum_filenames_are_rejected(self):
        source=self.release_set();windows=next((source/'windows').glob('*.zip'));windows.unlink()
        linux=next((source/'linux').glob('*.tar.gz'));target=source/'windows'/linux.name
        target.write_bytes(linux.read_bytes());(target.parent/'SHA256SUMS').write_text((linux.parent/'SHA256SUMS').read_text())
        with self.assertRaises(ValueError):assets.assemble(source,self.root/'out',self.manifest['version'],self.manifest['commit'])
        with self.assertRaisesRegex(ValueError,'Duplicate'):assets.write_checksums([linux,target],self.root/'sums')
