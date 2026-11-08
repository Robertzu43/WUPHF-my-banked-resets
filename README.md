<p align="center">
  <img src="https://raw.githubusercontent.com/Robertzu43/WUPHF-my-banked-resets/wuphf-initial/docs/images/wuphf-logo.svg" width="144" alt="WUPHF pixel-art logo">
</p>
<h1 align="center">WUPHF! for Codex Banked Resets</h1>
<p align="center"><strong>Your reset bank called. It wants you to use it.</strong></p>
<p align="center">Free, open-source reminders for your banked Codex resets. Your computer. Your accounts. Your choice of channels.</p>
<p align="center">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/tag/v0.1.0-beta.2"><img alt="Version 0.1.0-beta.2" src="https://img.shields.io/badge/version-0.1.0--beta.2-2454dd?style=flat-square"></a>
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-2454dd?style=flat-square"></a>
  <img alt="macOS, Windows and Linux" src="https://img.shields.io/badge/desktop-macOS%20%7C%20Windows%20%7C%20Linux-2454dd?style=flat-square">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/actions"><img alt="Build and test results" src="https://img.shields.io/badge/checks-GitHub%20Actions-2454dd?style=flat-square"></a>
</p>
<p align="center">
  <a href="#let-codex-set-it-up-for-you"><strong>Set up with Codex</strong></a> ·
  <a href="docs/user-guide.md"><strong>Full user guide</strong></a> ·
  <a href="#install-and-get-started"><strong>Install manually</strong></a> ·
  <a href="#connect-your-own-accounts"><strong>Connect your accounts</strong></a> ·
  <a href="#help-and-troubleshooting"><strong>Get help</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/tag/v0.1.0-beta.2"><strong>Release notes</strong></a>
</p>

WUPHF checks your available **banked Codex resets** and reminds you before known expiry dates. It never uses a reset for you. Choose **Gmail, other email, Telegram, calendar dates, or any combination**. There is no WUPHF account or hosted reminder service to sign up for.

A banked reset is a one-time reset saved to your Codex account for you to use before it expires. WUPHF watches that expiry, not your normal five-hour or weekly usage refresh. [Read OpenAI's explanation](https://help.openai.com/en/articles/20001498-how-resets-work-in-codex).

**New here?** The [full user guide](docs/user-guide.md) explains which option to choose, installation on each supported computer, every connection, reminder settings, calendar imports, daily use, troubleshooting and removal. Its [setup checklist](docs/user-guide.md#6-check-that-setup-is-complete) helps you verify that your own installation works.

## Let Codex set it up for you

Copy the prompt below into a **local Codex session on the computer that will run WUPHF**. Codex can handle the technical setup when that session has terminal and browser access. You choose the channels and complete any required sign-in or permission prompts. No passwords or bot tokens belong in the chat.

```text
Install and configure WUPHF for Codex Banked Resets on this computer for me.
Official project: https://github.com/Robertzu43/WUPHF-my-banked-resets
Setup guide: https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/user-guide.md

Do the setup work using your available tools. First check that you can access
my local computer; a cloud workspace cannot install my local background job.
If local access is unavailable, explain the smallest step I need to take.

Ask which options I want: Gmail, other email (SMTP), Telegram, Google Calendar
sync, or an ICS calendar file. I can choose one or several. Offer reminders
starting 7 days before expiry and repeating every 24 hours, and let me change
those settings and the interface language. Preserve existing settings unless
I request changes.

Detect my OS and architecture. Read the official setup guide and release notes.
Use the newest published compatible release, including betas, verify its
archive against that release's SHA256SUMS. Pin that version and use its own
setup instructions throughout. If the verified bundle provides --install, run
that local action and reopen the installed copy at the reported permanent
user-owned location; otherwise place the complete folder there yourself. Use the source-install instructions if no
compatible package exists; explain any untested compatibility. Check the
Codex CLI and help install it from its official source if missing. Use my own
ChatGPT sign-in without exposing its credentials or consuming any reset.

Open WUPHF's local setup page and configure only my selected options with my
own accounts. Keep the setup process running through browser authorization.
Guide me to enter private tokens/passwords directly in WUPHF, never in chat,
logs or committed files. Pause for sign-in and approvals that require me.
For Telegram, guide creation of my own bot and use WUPHF's pairing flow.
If a provider blocks connection, explain the exact issue and continue with
my other selected options. Never disable OS security protections.

Save my settings. Send one labeled test through each selected notification
channel and ask me to confirm receipt. For Calendar sync, verify a sync;
for ICS, export the file and help me import it. Enable background checks for
ongoing reminders/sync, avoiding duplicate jobs. If a job already exists, verify
its command targets this installed copy; replace an obsolete job through
Disable/Enable while preserving settings. For ICS-only setup, leave background
checks off. Verify the scheduler when enabled and the
last successful check; do not claim delivery from provider acceptance alone.

Finish with a short checklist of what is installed, connected, tested or still
blocked, how to reopen WUPHF and how to stop it. Explain that this computer
must stay awake, online and logged in. Make no purchases or paid subscriptions.
```

This is guided setup, not an unattended installer: sign-in, private credential entry, OS approvals and provider restrictions can still require your participation. If you prefer to install manually, follow the steps below.

## Install and get started

### 1. Sign in to Codex

Install the [official Codex CLI](https://developers.openai.com/codex/cli/), run `codex`, and choose **Sign in with ChatGPT** for the account you want to monitor. Confirm `codex --version` works in your terminal. WUPHF reads that local sign-in; you do not enter your ChatGPT password into WUPHF.

Already using the Codex CLI? You can keep your existing sign-in. The Codex desktop app alone does not replace this CLI requirement.

### 2. Download WUPHF for your computer

**The packages below include Python. You do not need to install Python separately.**

| Computer | Download | Open after extracting |
| --- | --- | --- |
| Mac with Apple silicon (M1 or newer) | [Download for macOS](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.2/wuphf-0.1.0-beta.2-macos-arm64-unsigned.tar.gz) | Open `Start WUPHF.command` in the complete extracted folder. |
| Windows 10 or newer, x64 | [Download for Windows](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.2/wuphf-0.1.0-beta.2-windows-x86_64-unsigned.zip) | Extract all files, then double-click `WUPHF.exe`. |
| Linux x64 desktop (Ubuntu 24.04 build) | [Download for Linux](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.2/wuphf-0.1.0-beta.2-linux-x86_64-unsigned.tar.gz) | Extract with `tar -xzf ARCHIVE_NAME.tar.gz`, then use `Start WUPHF.sh` in the complete folder. |

**Optional permanent install:** from the extracted folder run `./WUPHF --install` on Mac/Linux, or `.\WUPHF.exe --install` in Windows PowerShell. It copies the verified bundle into your user installation folder and prints how to reopen it. An identical installation is left alone; a different existing installation is refused with upgrade guidance. It does not configure accounts or enable jobs.

Keep the **whole extracted folder** together, including `_internal`, in a permanent location. Background checks use that location. On macOS, put the folder under `~/Library/Application Support/` before opening it; keep both WUPHF and Codex outside Documents, Desktop and Downloads for background operation. In Finder, **Go → Go to Folder** lets you open `~/Library/Application Support/`.

Linux requires a graphical session, a running **systemd user service**, and an unlocked **Secret Service keyring**. These are desktop packages, not cloud/server installers. Other architectures, including Intel Macs, can try the [source installation](#run-from-source) with Python 3.11+; compatibility outside the tested builds is not established.

Because this beta is unsigned, your operating system may ask you to approve opening it or block it. Review the download source and [SHA256SUMS](https://github.com/Robertzu43/WUPHF-my-banked-resets/releases/download/v0.1.0-beta.2/SHA256SUMS). On macOS, follow [Apple's instructions for opening an app from an unidentified developer](https://support.apple.com/en-us/102445) if you choose to trust the download. Do not disable system security protections globally. Source installation is also available below.

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

The file is a **snapshot**, not a subscription: it does not automatically update. Review imported events and alarms in your calendar app. Re-importing can create duplicates depending on the app. See [import steps for Google Calendar, Apple Calendar and Outlook](docs/user-guide.md#calendar-file-ics). Calendar alarms are separate from your email/Telegram reminder frequency.

### Google Calendar: automatic sync

1. Click **Connect Google** in the calendar section. Choose **your Google account** in a browser on the same computer.
2. Review the separate permission to create secondary calendars and manage their events. This is independent of Gmail; you can use Calendar alone.
3. Return to WUPHF and click **Sync now**. WUPHF creates its own calendar for known reset expiry dates. Enable background checks to keep it synced.

The bundled registration is used automatically; no client file is needed for that path. For your own registration, enable the Calendar API and select a **Desktop app** client JSON under **Developer setup** before connecting. See the [Google setup guide](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/google-production.md).

Events can remain after a reset is used or expires; remove old events manually. Disconnecting removes local authorization, not the remote calendar. Reconnecting can create another WUPHF calendar. Live authorization, saved-token refresh, and test-event creation/update were verified; longer unattended operation and the full reconnect lifecycle remain beta checks.

Google Calendar sync requires a stable Codex account identifier. Missing identity pauses sync; other channels and ICS remain available. Connections made before account binding require disconnect/reconnect once; existing remote calendars and events are retained.

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

Install Python **3.11+** and the signed-in Codex CLI. [Download the beta source ZIP](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/tags/v0.1.0-beta.2.zip) and extract it to a permanent folder. On macOS, keep the source, Python and Codex outside Documents/Desktop/Downloads.

- **macOS:** Open Terminal in the source folder and run `python3 -m wuphf.web`, or use `Start WUPHF.command`.
- **Windows:** Run `Start WUPHF.bat`; Python must be on PATH.
- **Linux:** Run `sh "Start WUPHF.sh"`. Your distribution may need its Python `venv` package.

The source launchers look for an already installed Python 3.11+ and validate a reused `.venv`. To select a particular interpreter, set `WUPHF_PYTHON` to its executable path. An old or broken environment is preserved with recovery instructions rather than deleted. The Windows/Linux source launchers create a local virtual environment and install the credential-storage dependency on first run, so internet access is required. The same account setup and background-check instructions above apply. The generated GitHub source ZIP is not included in the binary archive `SHA256SUMS`; verify its release tag/commit separately instead of applying a binary checksum to it.

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

`VERSION` identifies **0.1.0-beta.2**. Releases use Semantic Versioning with explicit beta tags. See the [changelog](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/CHANGELOG.md) and [release procedure](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/wuphf-initial/docs/releasing.md).

Run `python3 -m unittest discover -s tests -v` from the repository root. Install Node.js for the frontend behavioral checks. CI tests Python on macOS, Windows and Ubuntu; mocked provider tests do not establish live delivery.

To build on your target OS, use Python 3.11+ in a virtual environment, install `requirements.txt` and `pyinstaller>=6.17,<7`, then run:

```sh
python scripts/build_package.py --output /path/to/empty/dist --work /path/to/empty/build
python scripts/smoke_package.py /path/to/empty/dist/WUPHF
```

Linux builds also need `objdump` (usually `binutils`). Build-time internet access retrieves the exact CPython source notices; no runtime download is added. Packages include build information and third-party notices, including the Geist Pixel font's SIL Open Font License. Notice provenance is tracked; it is not exhaustive legal certification of every nested/static dependency. Maintainers verify archives and checksums before publication.
