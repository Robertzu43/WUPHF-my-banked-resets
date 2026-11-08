# Release readiness — 0.1.0-beta.1 candidate

Prepared November 7, 2026. This file is an evidence record, not a claim that a public release or Google approval exists.

## Decision

Prepare an unpublished beta candidate with Telegram as the primary tested route and Gmail as an experimental route while Google review is pending. Generic SMTP, Google Calendar sync and calendar-app imports are optional, not part of the verified beta claims. The user explicitly waived Windows and Linux real-device, real-account and clean-machine tests; automated tests and package checks remain required. WUPHF now bundles its registered public Desktop OAuth client, so ordinary Gmail setup no longer requires users to create a Cloud project. Google approval remains external.

## Fresh independent review

Three fresh agents audited tracking/reminders, security/integrations, and distribution/scheduling. A fourth independently reviewed the whole tool. Findings were reproduced with regression tests and fixed:

- Consolidate new and due reset reminders into one catch-up message per channel; preserve independent delivery history and retry state.
- Preserve reminder history for opaque reset IDs that share prefixes.
- Treat oversized numeric expiry timestamps as unknown instead of crashing.
- Bound Codex response waits even while notifications continue arriving.
- Bound setup HTTP workers and close stalled request connections.
- Keep scheduler failures visible and preserve recoverable job files; stop a Linux check when disabling its timer.
- Reset the Windows frozen-process DLL search directory once at startup, while retaining bundled Python dependency loading. Automated Windows package verification is required; this is not a claim about a real Windows Codex account.
- Avoid Windows default task conditions silently stopping checks on battery, without changing computer power settings.
- Keep a failed status refresh visibly unavailable when the interface language changes.
- Make the frozen macOS launcher discover conventional Homebrew-installed Codex commands when opened from Finder.
- Ensure frontend behavior checks run in CI and include version, setup documentation, build platform information and checksums with package artifacts.

## Evidence

Latest release-completion local validation: **251 tests passed** in 23.881 seconds on Python 3.14.7, including Node frontend checks. All documentation local links and whitespace checks passed. A fresh frozen macOS build passed asset and isolated background smoke checks; removing its public OAuth registration caused the expected asset-check failure. These results precede the new GitHub integration run; they do not replace it.

- Supported local interpreter: Python 3.14.7 on macOS 26.4 arm64.
- Full suite: **215 tests passed** in 23.412 seconds, including four Node frontend behavior checks. Command: `python -m unittest discover -s tests -v` using the packaging virtual environment.
- Fresh PyInstaller one-folder build completed successfully; packaged asset/version checks and isolated background smoke check passed.
- A temporary user-level launchd job ran the packaged candidate successfully against a synthetic Codex process with isolated data and no notification channels. The job was removed afterward. This verifies background execution on this Mac, not a clean install or real scheduled message delivery.
- The freshly built candidate performed a read-only real Codex snapshot and reported complete reset details. No message was sent by this diagnostic.
- A rebuilt package includes 30 Python/build-environment notice files with no missing distribution notices in the local build environment. Native library coverage remains separately qualified below.
- Documentation file links and `git diff --check` passed.
- GitHub matrix verification and final integration are recorded in PR #5. Local evidence does not substitute for those checks.

Release completion changes add a default Desktop OAuth registration with optional own-client override, exact-commit draft-only release automation, versioned archives and combined checksums, native binary notice inventories, and translated privacy/review disclosures. Calendar now uses the same bounded expiry validator as reminders. Independent auth and packaging reviews found no blocking defects; the asset-check coverage gap they identified was closed with a missing-registration regression test and actual frozen-build check. See [Google production setup](google-production.md) and the [release procedure](releasing.md).

Google Cloud was inspected on November 7: External / In production, verification required, one authorized user against the 100-user unverified cap. Gmail and Calendar APIs are enabled. Google still asks for 24 hours of propagation after homepage ownership verification before retrying branding. The published homepage and privacy policy were updated and fetched successfully. After the Mac was unlocked, a live refresh using the existing Gmail authorization succeeded. This confirms current refresh, not indefinite validity or new message receipt.

Earlier session evidence: the developer's account returned real banked-reset data, and the user confirmed receiving Gmail and Telegram test messages. The original developer Mac background job completed successfully at 21:11 America/Bogota on November 7 with no recorded error or channel failures. That job runs the earlier runtime; it does not prove the newly packaged candidate's scheduled delivery. No real resets were consumed during these checks.

The first release-completion commit (`c650eb6`) passed [all six CI test jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42447920340) and [all three package jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42447920277). Downloaded artifacts had valid checksums, manifests and notice references. That review identified wheel/framework attribution gaps and Windows UCRT copies from an unrelated build tool. The follow-up links exact distribution/framework provenance and builds for Windows 10+ using OS UCRT, preserving VC runtimes. Its native CI and final inventory verification must pass before binary publication.

## Remaining public-release conditions

| Condition | Status |
| --- | --- |
| Google branding/domain verification and scope review | Pending external Google review; the earlier ownership check requires time to propagate. Production OAuth status alone is not verification. |
| Simple public Gmail sign-in | Implemented with WUPHF's registered Desktop client in source and packages; own-client upload is optional. Google approval/warnings and unverified-user restrictions remain. |
| Current production authorization and refresh longevity | Earlier test email receipt plus a successful live refresh on November 7; indefinite token validity is not guaranteed. |
| Generic SMTP | Automated provider coverage only; no real SMTP-provider receipt claimed. |
| Google Calendar and ICS imports | Calendar API activated with owner approval. Bundled-client/own-client paths and ICS export are available. Automated coverage; live create/update/reconnect and calendar-app import not established. Stale events need manual removal. |
| New packaged Mac scheduled delivery and clean installation | Package/read-only checks are separate from installed scheduling; login, restart, sleep/wake and clean-machine coverage remain incomplete. |
| Windows/Linux real devices | Skipped by owner decision; not a release gate and not represented as passing. |
| Binary third-party notices | Exact-version CPython incorporated-software/hash-library notices, installed distribution notices, source-mapped Homebrew notices and byte-matched Debian copyright collection implemented. Fresh local Mac bundle: 53 native entries, zero unmatched entries, direct/extracted smoke and checksum verification passed. This is notice provenance, not legal certification; all three CI bundle inventories still need review before public binaries. |
| OS signing and compatibility | Packages are unsigned/unnotarized; build-info.json records the actual build platform. Older OS and alternate architecture compatibility is not established. |
| Language review | Eight catalogs and placeholder checks; native-speaker review pending. |
| Public release and downloads | Draft-only automation implemented: all three builds/tests/extraction checks and combined checksum verification precede draft creation. No automatic public publication. See release procedure and integration evidence for actual run status. |

## Known operating limits

The computer must be awake, online and logged in. Missing account identifiers prevent reliable account-switch detection and new-reset alerts. Incomplete detail snapshots pause reminders. Calendar exports are static, and Google events may remain after a reset disappears. Exceptionally large aggregated notifications may exceed a provider message limit and fail visibly; WUPHF does not split a catch-up into a message burst. Provider acceptance cannot guarantee device receipt.

## Publishing checklist

1. Select the reviewed integrated commit and require its automated test/package matrix to pass.
2. Resolve Google's public setup requirements, or deliberately publish a more limited preview with the experimental limitations prominently retained.
3. Complete the remaining advertised live integration/installation evidence or explicitly narrow supported claims; Windows/Linux real-device tests remain waived.
4. Create the prerelease tag only for that verified commit; attach the matching platform archives, build information and SHA-256 checksums. Keep unsigned status visible.
5. Verify the public downloads and the README's installation path. A stable release requires additional real-world beta evidence.
