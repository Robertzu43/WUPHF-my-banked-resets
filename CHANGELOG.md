# Changelog

## 0.1.0-beta.1 — Unreleased candidate

No version tag or public binary release has been published for this candidate. The [release readiness report](docs/release-readiness.md) tracks the remaining gates.

### Included

- Read-only Codex banked-reset tracking through the locally signed-in Codex CLI.
- Configurable reminder lead time and repeat interval; separate per-channel delivery state.
- Telegram pairing with a one-time phrase, Gmail send-only OAuth, and SMTP over SSL.
- Calendar snapshot export and experimental sync to an app-created Google calendar.
- Pixel-art interface with eight languages, keyboard focus and reduced-motion support.
- User-level background jobs for macOS, Windows and Linux; OS credential storage.
- Source launchers, experimental one-folder packages and automated CI.
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
- Real Windows/Linux account and background-delivery tests were skipped by the project owner's decision. Generic SMTP and live Google Calendar delivery are not confirmed.
- Calendar imports are static snapshots; Google events can remain after a reset disappears. Disconnecting does not remove remote calendars.
- Packages are unsigned and unnotarized; minimum OS compatibility and a clean-machine Mac installation are not established.

### Upgrade and removal

Disable checks before replacing or moving the app, preserve the data folder and OS credentials, then reopen, test and re-enable checks. To remove WUPHF, disable checks first, remove its OS credentials and `~/.local/share/wuphf-resets/`, and delete any unwanted Google calendar separately. See the [complete setup guide](README.md#installation-and-setup-preview).
