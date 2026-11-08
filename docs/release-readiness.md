# Release readiness — 0.1.0-beta.1

Updated November 8, 2026. This records the earlier verified binary candidate `472ebcc8a8a3b6a45766c0858ed2262fe90bf826` and its limits. Publication is a separate release action; Google approval is not claimed.

## Decision

Publish the beta with **all existing options**, as explicitly authorized by the owner: Gmail, Telegram, SMTP, calendar export and Google Calendar sync remain available; existing legacy ntfy configurations remain supported. Pending Google verification is a disclosed integration limitation, not a blocker for code or beta publication. The bundled Google Desktop registration identifies WUPHF; each user authorizes their own account and stores credentials on their own computer. An optional override using the user's own Desktop client remains available.

The owner waived Windows and Linux real-device, real-account and clean-machine tests. The automated matrices, package checks and final asset review below are complete. Claims remain limited to the evidence actually obtained; unsigned binaries, provider restrictions and untested paths are disclosed.

## Fresh independent review

Three fresh agents audited tracking/reminders, security/integrations, and distribution/scheduling. A fourth independently reviewed the whole tool. Findings were reproduced with regression tests and fixed:

- Consolidate new and due reset reminders into one catch-up message per channel; preserve independent delivery history and retry state.
- Preserve reminder history for opaque reset IDs that share prefixes.
- Treat oversized numeric expiry timestamps as unknown instead of crashing.
- Bound Codex response waits even while notifications continue arriving.
- Bound setup HTTP workers and close stalled request connections.
- Keep scheduler failures visible and preserve recoverable job files; stop a Linux check when disabling its timer.
- Reset the Windows frozen-process DLL search directory once at startup, while retaining bundled Python dependency loading. Automated Windows package verification passed; this is not a claim about a real Windows Codex account.
- Avoid Windows default task conditions silently stopping checks on battery, without changing computer power settings.
- Keep a failed status refresh visibly unavailable when the interface language changes.
- Make the frozen macOS launcher discover conventional Homebrew-installed Codex commands when opened from Finder.
- Ensure frontend behavior checks run in CI and include version, setup documentation, build platform information and checksums with package artifacts.

## Evidence

- Local release-completion validation: **251 tests passed** in 23.881 seconds on Python 3.14.7/macOS 26.4 arm64, including Node frontend checks. Documentation links and whitespace checks passed.
- [PR #9](https://github.com/Robertzu43/WUPHF-my-banked-resets/pull/9) merged at `472ebcc8a8a3b6a45766c0858ed2262fe90bf826`. All six [PR CI test jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42448568480), all three [PR package jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42448568443), and all jobs in the [exact-merged-commit draft workflow](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42448785875) passed.
- Direct and extracted package smoke checks passed on macOS, Windows and Linux; native Windows integration passed in CI.
- Final macOS arm64, Linux x86_64 and Windows x86_64 assets were independently downloaded and checked against uploaded GitHub digests and combined SHA-256 checksums. Manifests match `472ebcc`; archive layout, public registration fields and notice references were checked.
- Final native notice inventories contain Linux **65**, macOS **53** and Windows **18** entries, with zero unmatched entries and zero missing distribution notices. This establishes collected notice provenance, not exhaustive certification of nested or statically linked dependencies.
- Windows packages require **Windows 10+**, omit app-local UCRT/API-set copies and retain VCRUNTIME140.dll. Windows 7/8/8.1 are unsupported.
- The final macOS release executable read complete reset details from the real signed-in Codex account with exit 0. Existing plist and reminder-state fingerprints were unchanged immediately before/after this read-only check; no reset was consumed.
- A fresh extraction of the final macOS archive passed setup UI/session protection, font/eight-language assets, settings persistence (0600), ten-minute RunAtLoad plist generation, duplicate-install refusal, frozen background execution, synthetic failure/recovery and uninstall preserving settings. These used an isolated home, synthetic Codex and stub launchctl, not native scheduling or a clean machine.
- Earlier local checks included a temporary launchd job executing a packaged candidate against synthetic Codex with isolated data and no notification channels; the job was removed. A real frozen-build asset check also rejected a deliberately missing public OAuth registration.
- macOS ad-hoc signature integrity passed, but Gatekeeper assessment rejected the executable. There is no Developer ID signature or notarization. The tested extraction lacked browser quarantine, so browser-download onboarding is unverified.

Release completion changes add a default Desktop OAuth registration with optional own-client override, exact-commit draft-only release automation, versioned archives and combined checksums, native binary notice inventories, and translated privacy/review disclosures. Calendar now uses the same bounded expiry validator as reminders. Independent auth and packaging reviews found no blocking defects; the asset-check coverage gap they identified was closed with a missing-registration regression test and actual frozen-build check. See [Google production setup](google-production.md) and the [release procedure](releasing.md).

Google Cloud inspections on November 7–8 showed External / In production, verification required and a 100-user unverified cap. Gmail and Calendar APIs are enabled. Data Access declares Gmail send-only as sensitive and Calendar app-created as non-sensitive, with no restricted scopes. The Gmail justification is saved; the demonstration video URL is not yet supplied. At the November 8, 00:14 Bogotá check, Search Console showed the same account as verified owner, but fewer than 24 hours had elapsed and Branding still showed the earlier ownership issue. Public homepage and privacy policy were fetched successfully. These verification steps continue independently of beta publication.

Saved Gmail authorization refreshed successfully. Gmail and Telegram accepted fresh test messages; this is provider acceptance, not a fresh confirmation of device receipt. Earlier receipt was confirmed by the user. The existing Mac background job completed a successful November 8, 00:11 Bogotá check with no recorded errors or channel failures; its preserved earlier runtime does not prove newly packaged scheduled delivery.

After explicit owner consent, a live Calendar flow saved authorization in the OS credential store. A separate process using `472ebcc` source helpers refreshed it, created a WUPHF secondary calendar, created a labeled synthetic event, updated that same event by one hour and read back the expected ID, title and time with notifications disabled. Google Calendar UI inspection confirmed the event. The retained test event and saved calendar ID permit subsequent normal sync. The session's `WUPHF-calendar-live-check.json` and screenshot record this evidence; they are not distributed user data. This verifies source-helper API behavior and current refresh, not the packaged Calendar UI or later unattended refresh.

## Disclosed beta limitations and completed release checks

| Condition | Status |
| --- | --- |
| Google branding/domain verification and scope review | Pending; disclosed limitation, not a beta-publication gate. Unverified warnings, account restrictions and the 100-user cap remain. Production OAuth status is not approval. |
| Simple public Gmail sign-in | Implemented with WUPHF's registered Desktop client in source and packages; own-client upload is optional. Google approval/warnings and unverified-user restrictions remain. |
| Current authorization and refresh longevity | Gmail and Calendar saved-token refresh passed. Later unattended refresh and indefinite validity are not established. |
| Generic SMTP | Automated provider coverage only; no real SMTP-provider receipt claimed. |
| Google Calendar and ICS imports | Live source-helper calendar/event creation, same-event update, saved-token refresh and Google Calendar UI confirmation passed. Packaged Calendar UI, disconnect/reconnect and calendar-app imports remain unverified. Stale events need manual removal. |
| New packaged Mac scheduled delivery and clean installation | Package/read-only checks are separate from installed scheduling; login, restart, sleep/wake and clean-machine coverage remain incomplete. |
| Windows/Linux real devices | Skipped by owner decision; not a release gate and not represented as passing. |
| Binary third-party notices | All three final inventories reviewed: Linux 65, macOS 53, Windows 18 entries; zero unmatched entries or missing distribution notices. Nested/static coverage is not independently certified. |
| OS signing and compatibility | Packages are unsigned/unnotarized; build-info.json records the actual build platform. Older OS and alternate architecture compatibility is not established. |
| Language review | Eight catalogs and placeholder checks; native-speaker review pending. |
| Public release and downloads | Exact-commit draft workflow and final asset review completed. The owner authorized deliberate public beta publication with all options; automation itself remains draft-only. Check the release page for publication status. |

## Known operating limits

The computer must be awake, online and logged in. Missing account identifiers prevent reliable account-switch detection and new-reset alerts. Incomplete detail snapshots pause reminders. Calendar exports are static, and Google events may remain after a reset disappears. Exceptionally large aggregated notifications may exceed a provider message limit and fail visibly; WUPHF does not split a catch-up into a message burst. Provider acceptance cannot guarantee device receipt.

## Publication handoff

The earlier tested binary candidate is `472ebcc8a8a3b6a45766c0858ed2262fe90bf826`. The package-first README and own-account setup documentation are being integrated without runtime changes. Rebuild the archives from that reviewed documentation commit so the bundled README matches the release. Require its exact-commit workflow and checksum verification before publication; the release page and each package’s build-info.json identify the published commit. Verify public download availability and installation links. Google verification continues separately; it does not require removing any existing beta option. A stable release requires additional real-world evidence.
