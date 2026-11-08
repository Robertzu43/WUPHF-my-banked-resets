<p align="center">
  <img src="docs/images/wuphf-logo.svg" width="144" alt="WUPHF pixel-art logo">
</p>

<h1 align="center">WUPHF! for Codex Banked Resets</h1>

<p align="center"><strong>Your reset bank called. It wants you to use it.</strong></p>
<p align="center">A local, open-source reminder for the Codex banked resets you don't want to miss.</p>

<p align="center">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases"><img alt="Version: unreleased prototype" src="https://img.shields.io/badge/version-unreleased%20prototype-2454dd?style=flat-square"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2454dd?style=flat-square"></a>
  <img alt="Desktop: macOS, Windows and Linux preview" src="https://img.shields.io/badge/desktop-macOS%20%7C%20Windows%20%7C%20Linux-2454dd?style=flat-square">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/actions"><img alt="GitHub Actions" src="https://img.shields.io/badge/checks-GitHub%20Actions-2454dd?style=flat-square"></a>
</p>

<p align="center">
  <a href="#try-the-prototype"><strong>Get started</strong></a> ·
  <a href="#connect-your-channels"><strong>Connect notifications</strong></a> ·
  <a href="docs/superpowers/plans/2026-11-07-public-beta-release.md"><strong>Release plan</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/issues"><strong>Report an issue</strong></a>
</p>

> **Early prototype · No release published yet.** This development branch contains the cross-platform work under review. Windows and Linux passed automated checks; real-account and background-delivery tests were not performed. Google verification is pending. Keep a backup reminder until WUPHF is tested for your account.

WUPHF checks your available Codex banked resets and reminds you before known expiry dates through **email**, **Telegram**, or both. You can also add expiry dates to your calendar. WUPHF never uses a reset for you.

## What you can do

- See your available banked reset count and known expiry dates using your existing Codex CLI sign-in.
- Choose when reminders start and how often they repeat. Use any combination of supported channels.
- Export an `.ics` snapshot for Google Calendar, Apple Calendar, Outlook, and other compatible calendars. Experimental Google Calendar sync can add events to a separate WUPHF calendar.
- Use English, Spanish, German, Portuguese, French, Japanese, Korean, or Simplified Chinese. Translations are machine-assisted.

WUPHF runs locally. Your computer must be awake, online, and logged in for background checks and messages to run. Unknown or incomplete Codex data cannot be treated as a confirmed expiry or a used reset. Delivery depends on your selected services.

When Codex supplies an account identifier, WUPHF uses a local fingerprint to avoid carrying reminder state between different accounts. Codex may omit that identifier. While it is unavailable, WUPHF cannot send alerts for newly detected resets or reliably detect account or workspace switches; expiry reminders for known deadlines can still run. Check your account and reminders after switching, and keep a backup reminder.

## Try the prototype

These instructions describe the current **cross-platform development branch**, not a finished installer. Windows and Linux real-account tests have not been performed; the project owner chose not to require them for this release. For a more detailed walkthrough, see the [installation and setup guide](https://github.com/Robertzu43/WUPHF-my-banked-resets#installation-and-setup-preview).

1. Install [Python 3.11 or newer](https://www.python.org/downloads/) and the [Codex CLI](https://developers.openai.com/codex/cli/). On Windows, add Python to PATH during installation. Run `codex` and sign in with the ChatGPT account whose resets you want to track; verify that `codex --version` works in your terminal.
2. Download and unzip the [`feature/cross-platform` branch](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/heads/feature/cross-platform.zip). Keep the extracted folder in a permanent location: background checks need it to remain there. On macOS, keep WUPHF, its Python environment and Codex CLI outside Documents, Desktop and Downloads (for example in `~/Library/Application Support/WUPHF`); background installation blocks those protected folders. Other macOS privacy restrictions may still prevent checks, so confirm the background status after enabling.
3. Start WUPHF from that folder:
   - **macOS:** Double-click `Start WUPHF.command`. If macOS blocks the unsigned launcher, open Terminal in the folder and run `python3 -m wuphf.web`.
   - **Windows:** Double-click `Start WUPHF.bat`.
   - **Linux:** In a terminal, run `./Start\ WUPHF.sh`. A graphical session with an unlocked Secret Service keyring and systemd user services is required; some distributions also require the Python `venv` package.
4. In the setup page, choose your language and check that your banked reset status loads. Select the reminders and channels you want, then **Save settings**.
5. Use **Send test** for each messaging channel and confirm that the message arrives. Click **Enable checks** to start background monitoring; the setup page can then be closed.

Windows and Linux create a local Python environment and install the open-source `keyring` dependency the first time they run. The current launchers are not yet a polished installer.

## Connect your channels

Choose one or more. Save settings before testing. Never paste passwords, tokens, or OAuth client files into an issue or public chat.

### Gmail

1. Under **Gmail**, enter the Gmail address you will authorize.
2. The prototype currently needs a Google desktop OAuth client with the Gmail API enabled. In your Google Cloud project, enable the Gmail API, configure the consent screen, add yourself as a test user if required, and create a **Desktop app** OAuth client. Download its JSON file and select it under **Developer setup** if one is not already provided locally. See [Google’s setup guide](https://developers.google.com/workspace/gmail/api/quickstart/python) for the project steps. This file stays on your computer.
3. On the computer running WUPHF, click **Connect Gmail**, approve Google's send-only permission if you agree, and return to WUPHF. Save settings, send a test, and check your inbox.

Google may require app verification or restrict who can authorize a client. An app-owned, verified client for a simpler public connection is planned; don't assume this is finished. A Gmail connection in Codex or ChatGPT cannot be reused by this standalone app. A test email was received on the developer's Mac; background delivery and broader account coverage still need validation.

### Other email

Enable **Email** and enter your provider's SMTP SSL server and port, username, sender, recipient, and provider-compatible password or app password. Save and send a test. Provider requirements vary; the prototype supports SMTP over SSL, typically port 465.

### Telegram

1. In Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, and follow its prompts to create your own bot. Keep the resulting bot token private.
2. Enable Telegram in WUPHF and paste the bot token. Open your bot in Telegram and tap **Start**. In WUPHF, click **Generate pairing phrase**, then send that entire phrase to your bot in a private chat within 10 minutes.
3. Click **Find my chat ID**, then **Save settings**. Send a test. You can enter your private chat ID manually instead.

The optional lookup checks pending updates only when you click the button and does not confirm those updates. It accepts only an exact match for the current single-use pairing phrase in a private message. If multiple chats match, too many updates are pending, or a webhook or another bot client prevents polling, enter your private chat ID manually. Telegram was tested on the developer's Mac; broader delivery testing is still needed.

### Existing ntfy alerts

New setups offer email and Telegram. If an older installation already has ntfy configured, WUPHF shows a legacy control: uncheck it and save settings to stop those alerts. Its saved token remains in your operating system's credential store until you remove it there.

## Calendar

Click **Download .ics** and import the file into your calendar. This is a one-time snapshot; imported events do not update automatically when your resets change.

For experimental Google Calendar sync, select a Google desktop OAuth client with the Calendar API enabled under **Developer setup**, click **Connect Google**, authorize it if you agree, and click **Sync now**. WUPHF uses an app-created secondary calendar. Events can remain after a reset is used or expires; remove outdated events manually. Disconnecting removes local credentials and mappings but does not delete the calendar or its events. Live Google Calendar sync has not yet been verified.

## Privacy, stopping, and troubleshooting

Secrets are stored in the operating system's credential store: macOS Keychain, Windows Credential Manager, or Linux Secret Service. WUPHF rejects insecure plaintext keyring backends. Local state includes opaque reset identifiers; keep it private. Provider acceptance of a message does not guarantee receipt.

- **No status?** Confirm that the Codex CLI is installed, signed in to the intended account, and accessible from your session. If data or expiry details are unavailable, WUPHF cannot invent them.
- **No message?** Confirm that settings were saved, send a test, check the destination, and check the displayed error. Your computer and network must be available.
- **Want to stop checks?** Click **Disable**. To remove local data, delete the WUPHF credentials from your OS credential manager and `~/.local/share/wuphf-resets/` (under your user profile on Windows). Remove any WUPHF calendar separately in Google Calendar.
- **Need help?** Open an issue without including credentials, raw authentication files, or reset identifiers.

## Versioning and contributing

There are **no published releases or version tags yet**. The planned first public beta will use a pre-release tag such as `v0.1.0-beta.1`; stable releases will follow [Semantic Versioning](https://semver.org/) once the release checks pass. Development happens in pull requests; the cross-platform branch is not the default branch yet.

Contributions and translation corrections are welcome. Run the automated tests with `python3 -m unittest discover -s tests -v`. These tests use provider mocks and do not prove live delivery. Please review the [release plan](docs/superpowers/plans/2026-11-07-public-beta-release.md) before changing release behavior.

WUPHF is free and open source under the [MIT License](LICENSE). It is an independent project inspired by *The Office* and is not affiliated with OpenAI or the show.

### Experimental package builds

The repository can build **unsigned, unnotarized prototype** one-folder artifacts with PyInstaller; these are development checks, not published installers. Install Python 3.11+ and the signed-in Codex CLI first. Building on Linux also requires `objdump` (usually provided by `binutils`). In an isolated virtual environment, install `pyinstaller>=6.17,<7` and `requirements.txt`, then run:

```sh
python scripts/build_package.py --output /path/to/empty/dist --work /path/to/empty/build
python scripts/smoke_package.py /path/to/empty/dist/WUPHF
```

The smoke check uses a synthetic Codex process and temporary user directory. POSIX packages need an archive format that preserves symbolic links, such as `tar.gz`; do not use a ZIP that dereferences them. An experimental Mac build completed a read-only real Codex snapshot, but real reminder delivery and installed scheduling remain unverified. Linux real-Codex testing was not performed; Windows has an unresolved process-wide DLL search-path issue. The packages are not signed, notarized, or released.

For a read-only diagnostic, run the packaged executable with `--check-codex`. It checks whether Codex returns complete reset details without sending reminders.
