# Prepare an unsigned beta release

The manual **Draft unsigned beta release** workflow builds a reviewed commit on all three operating systems, runs the tests, validates extracted packages, combines SHA-256 checksums, and creates an **unpublished draft prerelease**. It never publishes automatically.

## Before drafting

1. Review the [readiness record](release-readiness.md), close code defects, and update `VERSION`, `CHANGELOG.md` and the README. A public beta must describe experimental integrations and unsigned packages accurately.
2. Merge the reviewed changes and require green test/package CI for the resulting commit. Use its full 40-character SHA, not a moving branch name.
3. Review each package's `build-info.json` and `third-party-notices/index.json`. Builds collect exact-version CPython source notices, installed distribution notices and supported native-library notices with provenance. They require internet access to the official CPython archive and stop if required source notices cannot be retrieved. The inventory explicitly lists unmatched native binaries; review and supply any required notices before distributing binaries publicly. Automated collection is not a license-compliance certification.

## Create the draft

In GitHub **Actions → Draft unsigned beta release → Run workflow**, select the repository default branch (`wuphf-initial`), enter the version from `VERSION` (currently `0.1.0-beta.1`) and the full reviewed commit SHA.

The GitHub CLI equivalent is:

```sh
gh workflow run draft-release.yml --ref wuphf-initial \
  -f version=0.1.0-beta.1 -f commit=FULL_40_CHARACTER_MERGED_SHA
```

The selected commit must belong to the default branch and have the same workflow files as the dispatch commit. Existing releases with the same version and tags pointing elsewhere stop the workflow. If uploads fail, inspect the partial draft before deciding whether to remove it and retry; the workflow will not overwrite it.

Each draft contains three versioned archives plus `SHA256SUMS`. Names include OS and the actual build architecture, for example:

```text
wuphf-0.1.0-beta.1-macos-arm64-unsigned.tar.gz
wuphf-0.1.0-beta.1-linux-x86_64-unsigned.tar.gz
wuphf-0.1.0-beta.1-windows-x86_64-unsigned.zip
SHA256SUMS
```

## Verify and publish deliberately

Download all assets, verify their hashes, extract them and preserve the entire `WUPHF` folder. Use `tar` for POSIX archives so executable modes and symbolic links survive. On macOS run `shasum -a 256 -c SHA256SUMS`; on Linux use `sha256sum -c SHA256SUMS`. On Windows compare `Get-FileHash .\ARCHIVE_NAME.zip -Algorithm SHA256` with the matching checksum row.

Check `build-info.json` against the selected SHA/version and smoke-test the extracted package. Windows/Linux real-device tests are waived by the owner, not claimed as completed. Google verification, signing, clean-machine installation and live delivery evidence must be disclosed separately from automated CI.

Only publish after reviewing the release conditions and final notes. Include supported architectures, dependencies (the signed-in Codex CLI remains required), unsigned status, setup, upgrade/removal instructions and known limits. Then verify the public download links and update README status. Draft creation may reserve a version tag; never reuse or move a published version. A stable release needs additional beta evidence.
