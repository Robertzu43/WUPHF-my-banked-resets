# Release readiness — 0.1.0-beta.1 candidate

Prepared November 7, 2026. This file is an evidence record, not a claim that a public release or Google approval exists.

## Decision

Prepare an unpublished beta candidate. The user explicitly waived Windows and Linux real-device, real-account and clean-machine tests; automated tests and package checks remain required. Gmail verification and a distributor-provided OAuth client are still external requirements for the promised simple public Gmail setup. Until those are resolved, Gmail and Google Calendar remain experimental, with a user-provided desktop OAuth client.

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

- Supported local interpreter: Python 3.14.7 on macOS 26.4 arm64.
- Full suite: **208 tests passed** in 22.942 seconds, including four Node frontend behavior checks. Command: `python -m unittest discover -s tests -v` using the packaging virtual environment.
- Fresh PyInstaller one-folder build completed successfully; packaged asset/version checks and isolated background smoke check passed.
- The freshly built candidate performed a read-only real Codex snapshot and reported complete reset details. No message was sent by this diagnostic.
- Documentation file links and `git diff --check` passed.
- GitHub matrix verification and final integration are recorded in PR #5. Local evidence does not substitute for those checks.

Earlier session evidence: the developer's account returned real banked-reset data, and the user confirmed receiving Gmail and Telegram test messages. The original developer Mac background job completed successfully at 21:11 America/Bogota on November 7 with no recorded error or channel failures. That job runs the earlier runtime; it does not prove the newly packaged candidate's scheduled delivery. No real resets were consumed during these checks.

## Remaining public-release conditions

| Condition | Status |
| --- | --- |
| Google branding/domain verification and scope review | Pending external Google review; the earlier ownership check requires time to propagate. Production OAuth status alone is not verification. |
| Simple public Gmail sign-in | No reviewed distributor OAuth client is bundled; fresh users still need a desktop client. |
| Current production authorization and refresh longevity | Test email receipt was confirmed earlier; durable refresh across time is not established by that receipt. |
| Generic SMTP | Automated provider coverage only; no real SMTP-provider receipt claimed. |
| Google Calendar and ICS imports | Automated coverage; live create/update/reconnect and calendar-app import not established. Calendar sync stays experimental and stale events need manual removal. |
| New packaged Mac scheduled delivery and clean installation | Package/read-only checks are separate from installed scheduling; login, restart, sleep/wake and clean-machine coverage remain incomplete. |
| Windows/Linux real devices | Skipped by owner decision; not a release gate and not represented as passing. |
| Binary third-party notices | Complete redistribution notice/license review for bundled Python, keyring dependencies and packaging runtime before public binaries. Source license and bundled font license are included. |
| OS signing and compatibility | Packages are unsigned/unnotarized; build-info.json records the actual build platform. Older OS and alternate architecture compatibility is not established. |
| Language review | Eight catalogs and placeholder checks; native-speaker review pending. |
| Public release and downloads | No public version tag, release assets or permanent download checksums published for this candidate. |

## Known operating limits

The computer must be awake, online and logged in. Missing account identifiers prevent reliable account-switch detection and new-reset alerts. Incomplete detail snapshots pause reminders. Calendar exports are static, and Google events may remain after a reset disappears. Exceptionally large aggregated notifications may exceed a provider message limit and fail visibly; WUPHF does not split a catch-up into a message burst. Provider acceptance cannot guarantee device receipt.

## Publishing checklist

1. Select the reviewed integrated commit and require its automated test/package matrix to pass.
2. Resolve Google's public setup requirements, or deliberately publish a more limited preview with the experimental limitations prominently retained.
3. Complete the remaining advertised live integration/installation evidence or explicitly narrow supported claims; Windows/Linux real-device tests remain waived.
4. Create the prerelease tag only for that verified commit; attach the matching platform archives, build information and SHA-256 checksums. Keep unsigned status visible.
5. Verify the public downloads and the README's installation path. A stable release requires additional real-world beta evidence.
