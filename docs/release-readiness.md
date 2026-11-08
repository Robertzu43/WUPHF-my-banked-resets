# Release readiness — 0.1.0-beta.2

Updated November 8, 2026. This candidate improves the existing local, independent-account beta. Publication and the final release-archive audit are separate gates; the published tag, build-info.json and SHA256SUMS identify the exact artifacts.

## Completed implementation and review

- Guided setup makes select → save → test → enable explicit in eight languages. Unsaved edits cannot test stale settings; tests record provider acceptance for the current session without claiming inbox/device receipt.
- Provider and scheduler action states reject stale responses, recover after failed actions and keep Disconnect reachable. Saved Gmail configuration is detected without reading keychain health, so missing credentials can be removed/reconnected. Errors do not falsely tell normal users to create a Google Cloud project.
- Banked resets, manual redemption, complete-zero versus unknown data, time zones, browser-read freshness, calendar imports and help are explained in the actual UI. Calendar-only saves have calendar guidance; incomplete exports stay in setup with an inline error.
- Packages contain complete offline help and Mac/Linux launch entries. The frozen local --install action validates and copies the complete bundle to a permanent user location, preserves trust metadata, refuses different existing destinations and uses exclusive promotion. Repeated identical installs are safe no-ops; no account, credential or scheduler setup is performed by installation.
- Source launchers select an existing compatible Python 3.11+, validate overrides and reused environments, preserve broken environments, and disable both modern and legacy Windows runtime acquisition during discovery.
- Calendar sync requires a stable Codex identity and refuses mismatched, unknown or legacy ownership before remote writes. Existing remote events are retained. Old connections require reconnect; other channels/ICS remain independent.
- Independent scoped packaging, setup, source-launcher, installer and whole-branch reviews found and drove fixes before sign-off. The final whole-branch review's two Google recovery defects were resolved at 933ba18022c2a60287c81dc58dfd565b29104a22. A fresh simulated-browser assessment scored the final reviewed candidate 8.5/10 overall (purpose 9, installation 7.5, channel setup 9, daily use 8.5, documentation 9). Its five original UI findings were resolved; final disconnect-failure retry was browser-tool blocked, while independent code/HTTP recovery tests passed. This is not measured novice success or a forced 10/10 rating.

## Automated and native evidence

Runtime candidate **933ba18022c2a60287c81dc58dfd565b29104a22** passed:

- [All six test jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42456131003): Python 3.11 and 3.13 on macOS, Windows and Ubuntu. An independent isolated-commit local run discovered 312 tests: 302 passed and ten native Windows cases were skipped on the Mac host; the CI matrix exercises the corresponding native platform cases.
- [All three package jobs](https://github.com/Robertzu43/WUPHF-my-banked-resets/actions/runs/42456131000): exact-commit frozen build, package layout/help, local installation/repeated installation, installed assets/version and synthetic Codex background checks. These use isolated homes and provider/job doubles, not users' accounts or native scheduled delivery.
- Native Windows regression cases verified Zone.Identifier stream preservation, source/destination root junction refusal, directory-link copying, and source-launcher flag isolation/restoration. This is CI execution, distinct from the owner-waived real-device tests.
- An additional Mac build at 3dca793 passed real frozen local install, original/installed repeat modes, installed-copy asset/version and synthetic Codex checks. Native Mac tests preserve quarantine attributes and test exclusive promotion/collision. These are diagnostic candidate checks, not the final downloadable release artifacts or a browser-quarantine approval walkthrough.
- Read-only live Codex inspection on the maintainer's current CLI returned complete details with a stable account identity. No reset was consumed and no raw account/reset data was published. This does not establish compatibility for every CLI/account.

Documentation and nonbehavioral copy completion commits may follow the tested runtime candidate. Final CI and release jobs must build and validate the selected immutable source commit; consult the release page for its exact workflow and artifact audit. Earlier beta.1 evidence below remains historical.

## Remaining limits and release conditions

- Google verification, unverified-app warnings and account limits remain. Production OAuth status is not approval. Google review does not block the owner-authorized beta publication.
- Binaries are unsigned/not Apple-notarized; no valid signing identity was available locally. No global security protections or quarantine metadata are removed. Normal per-app trust decisions can still be required.
- Clean first-time-user installation, actual browser-download trust approval, new-version provider receipt/import alarms, native installed scheduling, later token refresh and sleep/wake behavior are not established by these synthetic checks. Earlier Gmail/Telegram receipt and Calendar source-helper evidence are recorded below, not re-certified for beta.2.
- Windows/Linux real-device tests remain waived by the owner; they are not described as passed.
- A Calendar create followed by local persistence failure can leave an empty extra calendar. Existing/stale events and disconnected calendars require manual removal; automatic deletion is intentionally absent without unambiguous ownership and lifecycle evidence.
- Eight catalogs and automated placeholder/behavior tests are included; native-speaker and full assistive-technology validation remain pending.
- Final release gate: reviewed source, passing exact-commit CI, inspected versioned archives/notices/checksums, deliberate publication and public-download verification. This report does not replace those checks or prove a 10/10 outcome.

---

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
