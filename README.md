<p align="center">
  <img src="https://raw.githubusercontent.com/Robertzu43/WUPHF-my-banked-resets/wuphf-initial/docs/images/wuphf-logo.svg" width="144" alt="WUPHF pixel-art logo">
</p>
<h1 align="center">WUPHF! for Codex Banked Resets</h1>
<p align="center"><strong>Your reset bank called. It wants you to use it.</strong></p>
<p align="center">Free, open-source reminders for your banked Codex resets. Your computer. Your accounts. Your choice of channels.</p>
<p align="center">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/tag/v0.1.0-beta.1"><img alt="Version 0.1.0-beta.1" src="https://img.shields.io/badge/version-0.1.0--beta.1-2454dd?style=flat-square"></a>
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-2454dd?style=flat-square"></a>
  <img alt="macOS, Windows and Linux" src="https://img.shields.io/badge/desktop-macOS%20%7C%20Windows%20%7C%20Linux-2454dd?style=flat-square">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/actions"><img alt="Build and test results" src="https://img.shields.io/badge/checks-GitHub%20Actions-2454dd?style=flat-square"></a>
</p>
<p align="center">
  <a href="#install-and-get-started"><strong>Install</strong></a> ·
  <a href="#connect-your-own-accounts"><strong>Connect your accounts</strong></a> ·
  <a href="#help-and-troubleshooting"><strong>Get help</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/tag/v0.1.0-beta.1"><strong>Release notes</strong></a>
</p>

WUPHF checks your available **banked Codex resets** and reminds you before known expiry dates. It never uses a reset for you. Choose **Gmail, other email, Telegram, calendar dates, or any combination**. There is no WUPHF account or hosted reminder service to sign up for.

> **Public beta:** All listed options are included. Google verification is pending, so the bundled Google connection can show warnings or encounter access limits. Packages are unsigned/unnotarized. Keep a backup reminder while testing WUPHF with your account. These limitations do not require you to use the maintainer's accounts or wait to try another channel.

## Install and get started

### 1. Sign in to Codex

Install the [official Codex CLI](https://developers.openai.com/codex/cli/), run `codex`, and choose **Sign in with ChatGPT** for the account you want to monitor. Confirm `codex --version` works in your terminal. WUPHF reads that local sign-in; you do not enter your ChatGPT password into WUPHF.

Already using the Codex CLI? You can keep your existing sign-in. The Codex desktop app alone does not replace this CLI requirement.

### 2. Download WUPHF for your computer

**The packages below include Python. You do not need to install Python separately.**

| Computer | Download | Open after extracting |
| --- | --- | --- |
| Mac with Apple silicon (M1 or newer) | [Download for macOS](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.1/wuphf-0.1.0-beta.1-macos-arm64-unsigned.tar.gz) | In the `WUPHF` folder, run `./WUPHF` in Terminal. |
| Windows 10 or newer, x64 | [Download for Windows](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.1/wuphf-0.1.0-beta.1-windows-x86_64-unsigned.zip) | Extract all files, then double-click `WUPHF.exe`. |
| Linux x64 desktop (Ubuntu 24.04 build) | [Download for Linux](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.1/wuphf-0.1.0-beta.1-linux-x86_64-unsigned.tar.gz) | Extract with `tar -xzf ARCHIVE_NAME.tar.gz`, then run `./WUPHF` inside the extracted folder. |

Keep the **whole extracted folder** together, including `_internal`, in a permanent location. Background checks use that location. On macOS, put the folder under `~/Library/Application Support/` before opening it; keep both WUPHF and Codex outside Documents, Desktop and Downloads for background operation. In Finder, **Go → Go to Folder** lets you open `~/Library/Application Support/`.

Linux requires a graphical session, a running **systemd user service**, and an unlocked **Secret Service keyring**. These are desktop packages, not cloud/server installers. Other architectures, including Intel Macs, can try the [source installation](#run-from-source) with Python 3.11+; compatibility outside the tested builds is not established.

Because this beta is unsigned, your operating system may ask you to approve opening it or block it. Review the download source and [SHA256SUMS](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.1/SHA256SUMS). On macOS, follow [Apple's instructions for opening an app from an unidentified developer](https://support.apple.com/en-us/102445) if you choose to trust the download. Do not disable system security protections globally. Source installation is also available below.

### 3. Choose your reminders

WUPHF opens a setup page in your browser on **this computer**. Choose a language and confirm your banked-reset count appears. Connect only the options you want using the instructions below.

Set **Start reminders, days before** and **Repeat every, hours**, click **Save settings**, and use **Send test** for each notification channel. Confirm the test arrives before relying on reminders.

### 4. Turn on background checks

Click **Enable checks** under **Background checks**. Confirm the status is enabled and the last successful check updates. You can then close the setup page and its window.

Your computer must stay **awake, online, and logged in**. WUPHF checks approximately every 10 minutes; reminders follow the frequency you selected. Reopen WUPHF to change settings, inspect errors, or disable checks. For a one-time calendar export, background checks are not needed.

## Connect your own accounts

Every installation is independent. Your email sends your reminders, your Telegram bot delivers to your chat, and your calendar receives your events. Your credentials stay in your computer's operating-system credential store. The maintainer does not receive them or run your reminders.

| I want… | Choose… | What I need |
| --- | --- | --- |
| Reminders in my Gmail inbox | Gmail | My Google account; bundled connection subject to Google's pending review. |
| Reminders through another email provider | Email (SMTP) | My provider's SMTP SSL settings and app password or supported credential. |
| Messages in Telegram | Telegram | My own bot from BotFather and a private chat with it. |
| Dates in my preferred calendar | Download `.ics` | A calendar app that imports ICS files; no Google connection required. |
| Automatically synced Google Calendar dates | Connect Google | My Google account, authorized separately from Gmail. |

### Gmail

1. Enable **Gmail** and enter **your own Gmail address**. Use this same account when signing in.
2. Click **Connect Gmail**, choose your account, and review the send-only permission. WUPHF does not request permission to read your inbox.
3. Return to WUPHF, click **Save settings**, then **Send test**. Check your inbox.

Complete sign-in in a browser on the **same computer running WUPHF**. A phone cannot finish the local callback. If authorization times out, start again from WUPHF; old links expire.

**About Google verification:** WUPHF includes a shared Google **app registration**, not a shared email account. You still authorize and use your own Gmail. The registration is unverified: Google may display a warning, block authorization, or apply its unverified-user cap. A public beta does not imply Google approval or unlimited Google onboarding. You can choose another channel or configure your own Desktop app registration in **Developer setup**. An own-client setup has its own consent, policy and quota requirements; it is not a way to bypass Google's rules. [Google setup guide](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/google-production.md).

### Other email (SMTP)

1. Enable **Email**. Copy the **SMTP SSL server**, port (commonly `465`), username, sender address and app password or supported credential from **your email provider's instructions**.
2. Enter your destination email address. Save settings and send a test.

WUPHF supports SMTP over SSL; STARTTLS-only providers/ports are not supported in this beta. Do not enter your ordinary account password unless your provider explicitly requires it. SMTP does not use WUPHF's Google app registration.

### Telegram

1. Open [@BotFather](https://t.me/BotFather) in Telegram, send `/newbot`, and follow its instructions. Copy your new bot's token privately.
2. Enable **Telegram** in WUPHF and paste the token. Open **your bot's chat** and tap **Start**.
3. In WUPHF, click **Generate pairing phrase**. Send that exact phrase to your bot in a private chat within 10 minutes.
4. Click **Find my chat ID**, then **Save settings** and **Send test**. Confirm it arrives in Telegram.

You only create the bot once. Never share its token publicly. If automatic lookup fails, enter your private chat ID manually. A bot used by another service, a configured webhook, or multiple matching chats can prevent automatic pairing.

### Any calendar: ICS export

Click **Download .ics**, then import the file into Google Calendar, Apple Calendar, Outlook, or another compatible app. This works without connecting WUPHF to Google.

The file is a **snapshot**, not a subscription: it does not automatically update. Review imported events and alarms in your calendar app. Re-importing can create duplicates depending on the app.

### Google Calendar: automatic sync

1. Click **Connect Google** in the calendar section. Choose **your Google account** in a browser on the same computer.
2. Review the separate permission to create secondary calendars and manage their events. This is independent of Gmail; you can use Calendar alone.
3. Return to WUPHF and click **Sync now**. WUPHF creates its own calendar for known reset expiry dates. Enable background checks to keep it synced.

The bundled registration is used automatically; no client file is needed for that path. For your own registration, enable the Calendar API and select a **Desktop app** client JSON under **Developer setup** before connecting. See the [Google setup guide](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/google-production.md).

Events can remain after a reset is used or expires; remove old events manually. Disconnecting removes local authorization, not the remote calendar. Reconnecting can create another WUPHF calendar. Live authorization, saved-token refresh, and test-event creation/update were verified; longer unattended operation and the full reconnect lifecycle remain beta checks.

## Help and troubleshooting

| Problem | What to try |
| --- | --- |
| WUPHF cannot find Codex | Run `codex --version`, confirm your CLI sign-in, then reopen WUPHF. |
| Reset count or dates are unknown | Use **Refresh** and check the intended Codex account. Missing data is shown as unknown; WUPHF cannot invent expiry dates. |
| Google sign-in fails | Start a fresh connection on the same computer. Review the Google error; the bundled registration has pending verification and access limits. Other channels and ICS remain independent. |
| A test does not arrive | Save settings, send a test, check spam/your bot chat and the displayed error. Provider acceptance is not a delivery guarantee. |
| Background checks fail on Mac | Move WUPHF, Python (source installs) and Codex outside protected Documents/Desktop/Downloads locations; reopen and enable checks again. |
| Linux credentials or checks fail | Unlock the Secret Service keyring and use a graphical session with a systemd user service. |
| Need help | [Open an issue](https://github.com/Robertzu43/WUPHF-my-banked-resets/issues) with your OS, WUPHF version and a redacted error. Never include tokens, passwords or raw Codex auth/reset data. |

### Upgrade or uninstall

**Upgrade:** Disable background checks, close WUPHF, and replace its complete application folder with the new version. Keep your data folder and OS credentials. Reopen, review settings, send tests, then enable checks again. Do not run two copies against the same settings.

**Stop reminders:** Click **Disable** under Background checks. Settings and credentials remain saved; a check already in progress may finish.

**Remove WUPHF:** Disable checks first, disconnect Google integrations if used, and delete the app folder. To erase local data too, remove WUPHF entries from macOS Keychain, Windows Credential Manager, or Linux Secret Service, then delete `~/.local/share/wuphf-resets/` (inside your user profile on Windows). Remove WUPHF's calendar separately if desired. To revoke Google access remotely, use your [Google account connections](https://myaccount.google.com/connections).

## Run from source

<details>
<summary>For developers or users who prefer Python instead of a packaged download</summary>

Install Python **3.11+** and the signed-in Codex CLI. [Download the beta source ZIP](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/tags/v0.1.0-beta.1.zip) and extract it to a permanent folder. On macOS, keep the source, Python and Codex outside Documents/Desktop/Downloads.

- **macOS:** Open Terminal in the source folder and run `python3 -m wuphf.web`, or use `Start WUPHF.command`.
- **Windows:** Run `Start WUPHF.bat`; Python must be on PATH.
- **Linux:** Run `sh "Start WUPHF.sh"`. Your distribution may need its Python `venv` package.

The Windows/Linux source launchers create a local virtual environment and install the credential-storage dependency on first run, so internet access is required. The same account setup and background-check instructions above apply.

</details>

## Privacy and beta limits

WUPHF is local, free software under the [MIT License](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/LICENSE). It never redeems resets. Credentials use macOS Keychain, Windows Credential Manager or Linux Secret Service; insecure plaintext keyrings are rejected. Settings, reset identifiers and reminder history stay in `~/.local/share/wuphf-resets/`. Your selected providers receive the messages/events necessary for their features. There is no central WUPHF account database or telemetry. [Privacy policy](https://robertzu43.github.io/WUPHF-my-banked-resets/privacy.html).

- Your computer must be awake, online and logged in. Missing expiry data, provider failures and offline time can prevent alerts.
- When Codex omits a stable account identifier, WUPHF cannot reliably detect account/workspace switches or send new-reset alerts; known-expiry reminders can still run. Check settings after switching accounts.
- Gmail and Telegram test receipt were confirmed. Calendar authorization and live test-event create/update passed. Generic SMTP receipt, actual ICS imports, long-running sleep/wake behavior and clean-machine installation remain unverified.
- Windows/Linux have automated test/build coverage; real-device tests were waived, not claimed as passed. Packages cover the architectures listed above; older OS compatibility is not established. Mac binaries are ad-hoc signed, not Developer ID signed or notarized, and can be blocked by Gatekeeper.
- Eight languages are included: English, Spanish, German, Portuguese, French, Japanese, Korean and Simplified Chinese. Translations are machine-assisted; native-speaker corrections are welcome. Keyboard focus and reduced-motion support are included.
- Existing ntfy configurations remain available for their owners; new setup focuses on email, Telegram and calendars.

See the [release evidence](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/release-readiness.md) for the precise test scope. WUPHF is independent and is not affiliated with OpenAI or *The Office*.

## Development and versioning

`VERSION` identifies **0.1.0-beta.1**. Releases use Semantic Versioning with explicit beta tags. See the [changelog](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/CHANGELOG.md) and [release procedure](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/releasing.md).

Run `python3 -m unittest discover -s tests -v` from the repository root. Install Node.js for the frontend behavioral checks. CI tests Python on macOS, Windows and Ubuntu; mocked provider tests do not establish live delivery.

To build on your target OS, use Python 3.11+ in a virtual environment, install `requirements.txt` and `pyinstaller>=6.17,<7`, then run:

```sh
python scripts/build_package.py --output /path/to/empty/dist --work /path/to/empty/build
python scripts/smoke_package.py /path/to/empty/dist/WUPHF
```

Linux builds also need `objdump` (usually `binutils`). Build-time internet access retrieves the exact CPython source notices; no runtime download is added. Packages include build information and third-party notices, including the Geist Pixel font's SIL Open Font License. Notice provenance is tracked; it is not exhaustive legal certification of every nested/static dependency. Maintainers verify archives and checksums before publication.
