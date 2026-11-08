# WUPHF Public Beta Release Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans. Complete the tasks in order; use fresh review where tasks can be independently checked. This is a plan, not evidence that the release is ready.

**Goal:** Deliver a free, open-source beta that makes it easy for Codex users on Windows, macOS and supported Linux desktops to monitor banked resets and receive reminders through their chosen channels.

**Architecture:** Keep the existing local Python application, Codex CLI app-server integration, operating-system credential stores and user-level background jobs. Improve setup and packaging without introducing a central server or sharing secret bot credentials; expose failures and incomplete reset data honestly.

**Tech stack:** Python 3.11+, existing HTML/JavaScript UI, launchd, Windows Task Scheduler, systemd user services, OS credential stores, GitHub Actions.

**Spec:** The approved original product specification is `docs/superpowers/specs/2026-11-07-original-product-spec.md`. This plan updates its macOS-only first-release constraint to the user's later requirement: Windows, macOS and supported Linux. Its requested Sign in with ChatGPT integration was investigated; use the signed-in Codex CLI unless a supported alternative is proven to read banked resets.

## Global constraints

- Users can select any combination of Telegram, Gmail/SMTP, ntfy, and calendar; calendars alone remain valid.
- Never consume a reset, invent an expiry, treat incomplete results as zero, leak credentials, or promise delivery.
- Keep credentials in supported OS secure stores; no public shared Telegram bot token or centralized user database.
- Background checks require an awake, online, logged-in computer; explain that the computer may sleep and checks cannot run then.
- Do not send real messages or create real calendar events without the destination owner's authorization.
- Account, Google review, operating-system signing, and actual-device access are external dependencies; never mark them complete from mocked tests.

## Review focus

- Incomplete Codex detail rows, missing expiry, stale account data, and account switches cannot trigger false claims or destructive calendar updates.
- Sleeping, offline, signed-out or restarted computers produce clear status and at most one current catch-up reminder per channel, not a burst.
- Expired/revoked provider credentials or failed sends remain visible and retry safely without exposing secrets.
- Repeated sync, calendar deletion, and incomplete snapshots cannot create duplicates or remove unrelated events.
- Fresh installs, upgrade and uninstall on each supported platform preserve user data intentionally and never silently change power settings.

## Current baseline

The original developer Mac read real Codex data and received Gmail and Telegram tests. The current cross-platform branch has 102 automated tests passing in CI across macOS, Windows and Ubuntu on Python 3.11 and 3.13. A Windows runner exercised Credential Manager and Task Scheduler registration; a Linux container exercised Secret Service. None of these establishes full reminder delivery on real Windows/Linux accounts. The public repository has no releases or tags; PRs #2–#5 are stacked, with #3–#5 drafts. Google verification and production Gmail reauthorization remain outstanding, and Google Calendar live sync and ntfy phone delivery have not been established.

## Task 1: Establish a safe baseline and integrate changes

**Files:** `wuphf/core.py`, `wuphf/reminders.py`, `wuphf/runner.py`, `tests/test_core.py`, `tests/test_reminders.py`, `tests/test_runner.py`; PRs #2–#5.

- [ ] Review each stacked PR in order, verify its base, and resolve review findings without disturbing the developer's active Mac installation.
- [ ] Check the baseline tests with `python3 -m unittest discover -s tests -v`; require a passing GitHub Actions matrix for the proposed release commit.
- [ ] Verify that an incomplete snapshot never indicates a consumed reset or triggers an expiry reminder with no known expiry; add targeted tests if a case is missing.
- [ ] Merge in dependency order only after each PR's review and required checks pass. Record the resulting default-branch commit.

## Task 2: Reliable tracking and background reminders

**Files:** `wuphf/core.py`, `wuphf/reminders.py`, `wuphf/runner.py`, `wuphf/platform_jobs.py`, `wuphf/cli.py`, `wuphf/web.py`, `tests/test_reminders.py`, `tests/test_runner.py`, `tests/test_platform_jobs.py`.

- [ ] Test known expiry, changed expiry, unknown/missing/capped data, time-zone changes, account change, and an unavailable Codex CLI against the approved spec. Verify that the UI displays last successful check, failures and stale data accurately; implement any missing behavior.
- [ ] Using a controllable clock, test configured lead time and repeat interval, restart persistence, per-channel successes/failures, offline recovery and at most one catch-up per channel. Fix missing coverage or behavior.
- [ ] On each supported OS, enable background checks, log out/in, restart, sleep/wake, disconnect/reconnect network and disable/uninstall. Verify actual scheduler execution and status, not only registration. Record OS versions and observations; never change power settings without consent.
- [ ] Compare a live account snapshot with Codex's own display without consuming a reset. A real state change is needed to confirm real new/used/expired behavior; otherwise record that as unverified.

## Task 3: Google OAuth and calendar

**Files:** `wuphf/gmail_auth.py`, `wuphf/google_auth.py`, `wuphf/google.py`, `wuphf/web.py`, `wuphf/web.html`, `tests/test_gmail_auth.py`, `tests/test_google.py`, `README.md`.

- [ ] Inspect the existing Google Cloud project and verification status. Complete the consent-screen details, required policies, branding, scopes and verification submission Google actually requests; record pending external review and never imply approval before it arrives.
- [ ] Configure a distributor-owned desktop OAuth client and enabled APIs for Gmail and Calendar; supply public-client configuration safely, without publishing refresh tokens or private account data. Confirm Google's requirements for desktop OAuth and the requested scopes. Keep the optional own-client path documented.
- [ ] On the developer's Mac, initiate a fresh production Gmail authorization with a live local callback, confirm that credentials persist, and send an authorized test. Recheck token refresh over time; production status alone does not guarantee indefinite authorization.
- [ ] With a consented test account, create an app-owned calendar, sync twice, update an expiry, revoke/reconnect and verify no duplicates or edits to unrelated calendars. Implement and test safe cleanup only when a complete snapshot supports it; otherwise keep the current manual-cleanup limitation explicit.
- [ ] Import `.ics` into a popular calendar and confirm date/time and one-time snapshot semantics. Record the real-account evidence and remaining Google review blockers.

## Task 4: Simplify and verify channels

**Files:** `wuphf/channels.py`, `wuphf/web.html`, `wuphf/web.py`, `wuphf/translations.json`, `tests/test_channels.py`, `tests/test_web.py`, `tests/test_i18n.py`, `README.md`.

- [ ] Walk through Gmail, SMTP, Telegram and ntfy with a new user; identify every required field and failure. Add concise, translated, step-by-step inline help and test actions for saved destinations.
- [ ] Simplify Telegram setup using a user's own bot and a safe way to obtain the chat ID. Verify any auto-discovery against the Bot API and avoid shipping a shared secret. Document unavoidable BotFather and start-chat steps; do not promise one-click setup without a tested implementation.
- [ ] Test provider errors, invalid credentials and timeout handling with mocks; ensure no tokens appear in responses, logs or issue templates.
- [ ] With authorized destinations, receive real Telegram, Gmail, SMTP and ntfy messages on the intended devices and exercise a scheduled reminder for each enabled channel. Keep the beta blocked for any advertised channel without an end-to-end test, or explicitly exclude it from beta claims.

## Task 5: Easy installation and release packages

**Files:** `Start WUPHF.command`, `Start WUPHF.bat`, `Start WUPHF.sh`, `requirements.txt`, `.github/workflows/`, `README.md`; add platform packaging files only when needed.

- [ ] Test a clean-machine install for each OS with a person unfamiliar with the project. Record prerequisites and where each person gets stuck. Choose the smallest supported packaging approach that removes Python setup where practical, with a transparent Codex sign-in flow.
- [ ] Produce and verify packages for Windows, macOS and supported Linux; document architectures, OS floors, dependency/licenses, upgrade/uninstall and checksum generation. Test install, start, monitoring, upgrade, and uninstall without deleting credentials or state unexpectedly.
- [ ] Assess OS signing/notarization availability and costs; sign where feasible and document warnings and the exact unsigned status otherwise. Do not advertise a polished universal installer before it exists and is tested.

## Task 6: Documentation, versioning and accessibility

**Files:** `README.md`, `docs/images/wuphf-logo.svg`, `docs/superpowers/plans/2026-11-07-public-beta-release.md`; add `CHANGELOG.md` at release.

- [ ] Keep README logo, plain-language overview, status, OS support, exact current setup, supported channels, calendar limitations, security, uninstall and troubleshooting accurate for the default branch. Ensure a new user can follow the final installation steps without private context.
- [ ] Confirm each of the eight translations, keyboard navigation, visible focus, reduced-motion behavior and readable contrast. Record native-speaker review as pending if unavailable.
- [ ] Adopt Semantic Versioning, create an initial `CHANGELOG.md`, and prepare `v0.1.0-beta.1` as a prerelease only when beta gates pass. Release notes must name supported systems, tested integrations, known limitations and upgrade/uninstall steps. Never create a tag for an unreleased or unverified build.

## Task 7: Release gate

- [ ] Confirm Task 1–6 evidence: merged commit, green CI, real reset tracking, actual background execution, delivered channel tests, calendar tests, working clean installs, privacy/security review and accurate documentation.
- [ ] Record outstanding third-party conditions, such as Google verification, signing, or device access, and resolve them or narrow the beta's supported claims explicitly. Avoid falsely representing Google approval or external service availability.
- [ ] Have an independent reviewer check the complete diff and release artifacts, then tag and publish the prerelease with its checksums and changelog. Verify public download and onboarding from a clean environment.
- [ ] After beta feedback, repeat the gate for a stable release; do not promise a stable date before the external dependencies and real-world tests pass.
