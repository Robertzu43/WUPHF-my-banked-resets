<p align="center">
  <img src="docs/images/wuphf-logo.svg" width="144" alt="WUPHF pixel-art logo">
</p>

<h1 align="center">WUPHF! for Codex Banked Resets</h1>

<p align="center"><strong>Your reset bank called. It wants you to use it.</strong></p>
<p align="center">A local, open-source reminder for the Codex banked resets you don't want to miss.</p>

<p align="center">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases"><img alt="Version: 0.1.0-beta.1 candidate (unreleased)" src="https://img.shields.io/badge/version-0.1.0--beta.1%20candidate-2454dd?style=flat-square"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2454dd?style=flat-square"></a>
  <img alt="Desktop: macOS, Windows and Linux preview" src="https://img.shields.io/badge/desktop-macOS%20%7C%20Windows%20%7C%20Linux-2454dd?style=flat-square">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/actions"><img alt="GitHub Actions" src="https://img.shields.io/badge/checks-GitHub%20Actions-2454dd?style=flat-square"></a>
</p>

<p align="center">
  <a href="#installation-and-setup-preview"><strong>Get started</strong></a> ·
  <a href="#3-choose-how-to-receive-reminders"><strong>Connect notifications</strong></a> ·
  <a href="docs/superpowers/plans/2026-11-07-public-beta-release.md"><strong>Release plan</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/issues"><strong>Report an issue</strong></a>
</p>

> **Release candidate · Not published yet.** Version `0.1.0-beta.1` is being prepared; see the [release readiness report](docs/release-readiness.md) for evidence and remaining gates. Windows and Linux passed automated checks; real-account and background-delivery tests were not performed. Google verification is pending. Keep a backup reminder until WUPHF is tested for your account.

WUPHF checks your available Codex banked resets and reminds you before known expiry dates through **email**, **Telegram**, or both. You can also add expiry dates to your calendar. WUPHF never uses a reset for you.

## What you can do

- See your available banked reset count and known expiry dates using your existing Codex CLI sign-in.
- Choose when reminders start and how often they repeat. Use any combination of supported channels.
- Export an `.ics` snapshot for Google Calendar, Apple Calendar, Outlook, and other compatible calendars. Experimental Google Calendar sync can add events to a separate WUPHF calendar.
- Use English, Spanish, German, Portuguese, French, Japanese, Korean, or Simplified Chinese. Translations are machine-assisted.

WUPHF runs locally. Your computer must be awake, online, and logged in for background checks and messages to run. Unknown or incomplete Codex data cannot be treated as a confirmed expiry or a used reset. Delivery depends on your selected services.

When Codex supplies an account identifier, WUPHF uses a local fingerprint to avoid carrying reminder state between different accounts. Codex may omit that identifier. While it is unavailable, WUPHF cannot send alerts for newly detected resets or reliably detect account or workspace switches; expiry reminders for known deadlines can still run. Check your account and reminders after switching, and keep a backup reminder.

## Installation and setup (preview)


These instructions run WUPHF from source. Python is required for this method; the experimental packaged builds include Python. Windows and Linux real-device tests were skipped at the project owner’s request; automated checks remain required.

### 1. Install the prerequisites

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/) or your platform's package manager. On Windows, allow the installer to add Python to your PATH. On Linux, your distribution may also require its Python `venv` package.
2. Install the **Codex CLI** by following the [official Codex CLI guide](https://developers.openai.com/codex/cli/). Open Terminal, PowerShell, or a Linux terminal and run `codex`; sign in with the ChatGPT account whose banked resets you want to monitor. WUPHF uses the CLI's existing sign-in.
3. Confirm that `codex --version` works in the terminal where you will start WUPHF. If the command isn't found, follow the Codex guide's installation and PATH instructions and reopen your terminal.

**Linux only:** A graphical desktop session with a running systemd user service and an unlocked Secret Service keyring is required. The Windows and Linux launchers create a local Python environment and install WUPHF's open-source credential-storage dependency on first run, so an internet connection is needed.

### 2. Download and open WUPHF

1. [Download the source preview as a ZIP](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/heads/wuphf-initial.zip), then extract it. This is an unpublished development preview, not a signed installer.
2. Move the extracted folder to a location where it can stay; background checks use that folder. On macOS, keep WUPHF, its Python executable and the Codex CLI outside **Documents**, **Desktop**, and **Downloads**. For example, use `~/Library/Application Support/WUPHF`. The preview blocks background installation from those folders; other macOS privacy settings can still affect execution.
3. Open the folder and start the launcher for your computer:
   - **macOS:** Double-click `Start WUPHF.command`. If macOS blocks the unsigned launcher, open Terminal in the folder and run `python3 -m wuphf.web`.
   - **Windows:** Double-click `Start WUPHF.bat`. Keep the window open while using the setup page.
   - **Linux:** Open a terminal in the folder and run `sh "Start WUPHF.sh"`.
4. WUPHF opens a local setup page in your browser. Choose a language and check that your available reset count appears. If it does not, check your Codex sign-in and use **Refresh**.

### 3. Choose how to receive reminders

You can use email, Telegram, or both. Set **Start reminders, days before** and **Repeat every, hours** to your preference. Save settings before sending a test.

#### Telegram

1. In Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, and follow its instructions to create a bot. Keep the bot token private.
2. In WUPHF, enable **Telegram** and paste the bot token. Open your new bot in Telegram and tap **Start**.
3. In WUPHF, select **Generate pairing phrase**. Send the entire phrase to your bot in a private chat within 10 minutes.
4. Select **Find my chat ID**, then **Save settings**. Select **Send test** and confirm the message arrives. You can enter your private chat ID manually if lookup is unavailable.

WUPHF matches the one-time phrase to a private message. If multiple chats match, Telegram has too many pending updates, a webhook is configured, or another bot client is using updates, use the manual chat ID. Never post your bot token in an issue or chat.

#### Gmail (experimental)

The current preview **does not yet offer a universal one-click Gmail setup**. Google verification is pending, and a fresh installation currently needs its own Google desktop OAuth client. Telegram or the SMTP option below can be used while this is being completed.

If you already have a suitable Google Cloud project:

1. Enable the **Gmail API** in that project and configure the Google Auth consent screen. If your app is in testing, add your Google account as a test user where required.
2. In Google Auth Platform, create an OAuth client of type **Desktop app** and download its JSON file. Google's [desktop client setup instructions](https://developers.google.com/workspace/gmail/api/quickstart/python) explain the Google Cloud steps. Keep the JSON file private.
3. In WUPHF, enable **Gmail** and enter the same Gmail address you will authorize. Under **Developer setup**, select your downloaded desktop OAuth client JSON, then click **Connect Gmail**.
4. On **the same computer running WUPHF**, choose your Google account and approve the send-only permission if you agree. Return to WUPHF, click **Save settings**, and use **Send test**. Check the inbox to confirm receipt.

Google may display an unverified-app warning or restrict access depending on the client and consent-screen status. A saved connection alone does not prove delivery. Google verification and an app-owned client for simpler public setup are pending.

#### Other email (SMTP)

1. Enable **Email**. Obtain your provider's **SMTP SSL server**, port, username, sender address and app password or other provider-compatible credential from the provider's instructions. WUPHF currently supports SMTP over SSL, commonly port `465`.
2. Enter those details and the destination email address in WUPHF. The app password is stored in your operating system's credential store.
3. Select **Save settings**, then **Send test**, and check the destination inbox. Provider settings and app-password requirements vary.

### 4. Enable and verify background reminders

1. Under **Background checks**, click **Enable checks**. Keep the extracted WUPHF folder in the same location afterwards.
2. Check the displayed monitoring status and the time of the **last successful background check**. An enabled scheduler is not proof that a notification arrived; review any displayed errors and test each selected channel.
3. The setup page may be closed. Your computer must remain **awake, online, and logged in** for checks and notifications. Checks run approximately every 10 minutes; a delay, provider failure, or missing expiry information can prevent an alert.
4. If Codex does not supply an account identifier, WUPHF cannot reliably detect account or workspace switches or send alerts for newly detected resets. Expiry reminders for known deadlines can still run. Check your settings after switching accounts and keep a backup reminder.

### 5. Add dates to your calendar (optional)

Select **Download .ics** in WUPHF and import it into Google Calendar, Apple Calendar, Outlook, or another compatible calendar. The imported file is a **one-time snapshot**; it does not update automatically.

Experimental Google Calendar sync requires a Google desktop OAuth client with the Calendar API enabled. Select it under **Developer setup**, click **Connect Google**, authorize if you agree, and click **Sync now**. WUPHF creates a separate calendar; events may remain after a reset is used or expires and need manual cleanup. This integration has not yet been verified end to end with a live account.

### Troubleshooting and removal

- **WUPHF doesn't open:** Check Python and Codex CLI are installed and available in your session. On Linux, check the `venv` package, systemd user session and unlocked keyring. On macOS, move the project out of protected folders before enabling background checks.
- **No resets or dates:** Confirm the CLI is signed in to the intended account. If Codex does not supply details, WUPHF displays them as unknown; it cannot invent an expiry.
- **No notification:** Save settings, run **Send test**, check the destination and displayed error, and ensure your computer is awake and online. A provider accepting a message does not guarantee it reached your device.
- **Stop checks:** Click **Disable** under Background checks. This leaves your settings and credentials in place. On Windows, a check already in progress may finish.
- **Remove local data:** After disabling checks, remove WUPHF's entries from macOS Keychain, Windows Credential Manager, or Linux Secret Service, then remove `~/.local/share/wuphf-resets/` (under your user profile on Windows). Remove an app-created Google calendar separately if desired.
- **Need help:** [Open an issue](https://github.com/Robertzu43/WUPHF-my-banked-resets/issues). Never include tokens, passwords, OAuth client files, raw auth files, or reset identifiers.

## Upgrade safely

Before replacing or moving WUPHF, click **Disable** and close its setup process. Keep your existing data folder and OS credentials. Download the new source or package into its permanent location, reopen it, review your settings, send a test, then enable checks again. Do not run two copies against the same settings at once. If you move the app, reinstall its background job so it points to the new location.

## Privacy and limitations

WUPHF runs locally and never redeems a reset. It stores credentials in macOS Keychain, Windows Credential Manager, or Linux Secret Service; insecure plaintext keyring backends are rejected. Reset identifiers, settings and reminder history stay in `~/.local/share/wuphf-resets/`. Your chosen provider receives the notification contents. There is no central WUPHF account database or telemetry.

Gmail and Telegram test messages were received on the developer’s Mac. Generic SMTP delivery, live Google Calendar sync and imports into calendar applications remain unverified. Google Calendar sync is experimental: disconnecting removes local credentials and mappings, but leaves the calendar and its events in Google. Reconnecting can create a new WUPHF calendar.

An older ntfy configuration remains visible so its owner can disable it. New setups offer email and Telegram. Disabling a channel does not erase its saved secret; remove the WUPHF entry from your OS credential store to erase it.

Eight languages are available: English, Spanish, German, Portuguese, French, Japanese, Korean and Simplified Chinese. Translations are machine-assisted and have not received a complete native-speaker review. Keyboard focus and reduced-motion support are included.

## Versioning and development

[`VERSION`](VERSION) identifies the candidate: **0.1.0-beta.1**. It is not a published release. See the [changelog](CHANGELOG.md), [release readiness report](docs/release-readiness.md), and [implementation plan](docs/superpowers/plans/2026-11-07-public-beta-release.md). We use Semantic Versioning with explicit prerelease tags; a version badge is not evidence that an installer has shipped.

Run the checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

Install Node.js to include the frontend behavioral checks. CI requires Node and runs Python tests on macOS, Windows and Ubuntu. Tests use mocks for external providers; passing them does not prove live delivery. Contributions and translation corrections are welcome. Keep secrets and private reset identifiers out of bug reports.

### Build an experimental package

Build on the operating system you want to target. Use Python 3.11+ in an isolated virtual environment, install `requirements.txt` and `pyinstaller>=6.17,<7`, then run:

```sh
python scripts/build_package.py --output /path/to/empty/dist --work /path/to/empty/build
python scripts/smoke_package.py /path/to/empty/dist/WUPHF
```

Linux also requires `objdump` (usually from `binutils`). The one-folder package includes Python but still requires the signed-in Codex CLI; Linux also needs an unlocked Secret Service keyring and a systemd user session. Keep the whole package folder together. Run `WUPHF` (`WUPHF.exe` on Windows) inside it to open setup. `--version` shows its candidate version; `--check-codex` performs a read-only account check without sending messages.

These packages are **unsigned and unnotarized**. They are development artifacts, not universal installers. CI builds for its runner’s architecture; support for other architectures or older OS versions is not established. POSIX packages must use an archive format that preserves symbolic links, such as `tar.gz`; Windows packages use ZIP. A packaging smoke check uses temporary data and a synthetic Codex process. See the readiness report for exact build evidence and limitations. Packages include `third-party-notices/` with Python and build-environment distribution notices and an inventory; this is not an exhaustive native-library audit. Each CI artifact includes `SHA256SUMS` for its archive and `build-info.json` inside the package. On macOS verify with `shasum -a 256 -c SHA256SUMS`; on Linux use `sha256sum -c SHA256SUMS`; on Windows compare `Get-FileHash .\wuphf-beta.zip -Algorithm SHA256` with `SHA256SUMS`. Public release downloads will only appear when a release is actually published.

WUPHF is free and open source under the [MIT License](LICENSE). The bundled Geist Pixel font uses the [SIL Open Font License](wuphf/assets/geist-pixel-OFL.txt). WUPHF is an independent project inspired by *The Office* and is not affiliated with OpenAI or the show.
