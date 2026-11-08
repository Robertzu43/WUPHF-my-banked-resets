# Changelog

## 0.1.0-beta.3 — 2026-11-08

- Fix default HTTPS certificate verification in frozen macOS packages using system trust roots while preserving custom trust configuration.
- Reconcile newly managed Calendar events with ownership markers, saved-version checks and conditional updates/deletion; preserve legacy, edited and ambiguous events.
- Pause Calendar writes for invalid/incomplete reset data and report actionable conflicts in eight languages.
- Add nearby Save actions, an at-a-glance background-check summary and Calendar-only setup guidance.


## 0.1.0-beta.2 — 2026-11-08

- Guide channel setup through save, test and background checks, with unsaved-change protection and honest session test acceptance.
- Explain banked resets and manual redemption in the app; add guide/import help, explicit expiry time zones and read freshness in eight languages.
- Disable inapplicable provider actions, ignore stale authorization responses, and preserve setup during failed calendar exports.
- Include complete offline help and native Mac/Linux launch entries in packages.
- Bind Google Calendar sync to a stable Codex account; refuse ambiguous legacy or changed-account writes while preserving existing remote events. Older connections require reconnect, and missing stable identity pauses Calendar sync.
- Add frozen local installation with safe repeat behavior, native trust-metadata preservation, path/link validation and failure cleanup.
- Improve compatible Python discovery and preserved-environment recovery for source installations; verify native Windows regression cases in CI.


## 0.1.0-beta.1 — 2026-11-08

First public beta with independent setup for each user’s Gmail, SMTP email, Telegram and calendar accounts. Google verification remains pending; all existing options are included with their limitations disclosed. See the [release readiness report](docs/release-readiness.md).

### Included

- Read-only Codex banked-reset tracking through the locally signed-in Codex CLI.
- Configurable reminder lead time and repeat interval; separate per-channel delivery state.
- Telegram pairing with a one-time phrase, Gmail send-only OAuth, and SMTP over SSL.
- Calendar snapshot export and experimental sync to an app-created Google calendar.
- Pixel-art interface with eight languages, keyboard focus and reduced-motion support.
- User-level background jobs for macOS, Windows and Linux; OS credential storage.
- Platform downloads with Python included, a package-first installation guide, source launchers and automated CI.
- Bundled public Desktop app registration for Gmail and Calendar; normal setup no longer requires users to create a Google Cloud project.
- Draft-only release workflow with versioned OS/architecture archives, exact-commit checks and combined SHA-256 checksums.
- Public privacy policy linked in the app, with Google review status disclosed in eight languages.

### Reliability fixes

- Combine catch-up reminders per channel and preserve retry history for IDs with common prefixes.
- Reject invalid expiry numbers and bound Codex response waits.
- Limit local setup-server connections and stalled reads.
- Improve scheduler failure recovery, Windows battery operation and packaged Codex discovery.
- Clear stale reset status after refresh errors, including when changing language.
- Include candidate version, documentation, platform metadata and archive checksums.
- Keep Windows 10+ packages on the OS Universal C Runtime and exclude unrelated DLLs from build-tool PATH entries.
- Attribute native wheel binaries by exact distribution ownership and Python-framework OpenSSL libraries by build provenance.

### Known limits

- Google verification remains pending. Gmail and Calendar use the bundled registration but Google can warn or restrict access until approval.
- Computers must be awake, online and logged in. Missing account identifiers limit switch detection and new-reset alerts; incomplete details pause reminders.
- Real Windows/Linux account and background-delivery tests were skipped by the project owner's decision. Generic SMTP receipt remains unverified. Calendar authorization, saved-token refresh and live test-event create/update passed; longer unattended sync and reconnect remain unverified.
- Calendar imports are static snapshots; Google events can remain after a reset disappears. Disconnecting does not remove remote calendars.
- Packages are unsigned and unnotarized; minimum OS compatibility and a clean-machine Mac installation are not established.

### Upgrade and removal

Disable checks before replacing or moving the app, preserve the data folder and OS credentials, then reopen, test and re-enable checks. To remove WUPHF, disable checks first, remove its OS credentials and `~/.local/share/wuphf-resets/`, and delete any unwanted Google calendar separately. See the [complete setup guide](README.md#install-and-get-started).
