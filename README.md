<p align="center">
  <img src="docs/images/wuphf-logo.svg" width="144" alt="WUPHF pixel-art logo">
</p>

<h1 align="center">WUPHF! for Codex Banked Resets</h1>

<p align="center"><strong>Your reset bank called. It wants you to use it.</strong></p>
<p align="center">A local, open-source reminder for the Codex banked resets you don't want to miss.</p>

<p align="center">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/releases"><img alt="Version: unreleased prototype" src="https://img.shields.io/badge/version-unreleased%20prototype-2454dd?style=flat-square"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2454dd?style=flat-square"></a>
  <img alt="Cross-platform support in review" src="https://img.shields.io/badge/desktop-cross--platform%20preview-2454dd?style=flat-square">
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/actions"><img alt="GitHub Actions" src="https://img.shields.io/badge/checks-GitHub%20Actions-2454dd?style=flat-square"></a>
</p>

<p align="center">
  <a href="#installation-and-setup-preview"><strong>Installation &amp; setup</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/tree/feature/cross-platform"><strong>Cross-platform preview</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/feature/cross-platform/docs/superpowers/plans/2026-11-07-public-beta-release.md"><strong>Release plan</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/issues"><strong>Report an issue</strong></a>
</p>

> **Early prototype · No release published yet.** The default branch is the earlier macOS prototype. Windows, Linux, Gmail sign-in and the pixel interface are in the [cross-platform development branch](https://github.com/Robertzu43/WUPHF-my-banked-resets/tree/feature/cross-platform) and are not released. Google verification remains in progress. Windows and Linux passed automated checks, but real-account and background-delivery tests were not performed. Keep a backup reminder until WUPHF is tested for your account.

WUPHF helps you track available Codex banked resets and remember known expiry dates. The planned release focuses on **email** and **Telegram**, with calendar export available. You choose when reminders start and how often they repeat. WUPHF never uses a reset for you.

## At a glance

- **Stay informed:** View available banked resets and known deadlines from your signed-in Codex CLI.
- **Choose your WUPHF:** Configure email, Telegram, or both, and send a test to each destination.
- **Save the date:** Export an `.ics` snapshot for compatible calendars; the preview also includes experimental Google Calendar sync.
- **Keep it local:** Your computer runs the checks and stores credentials in its secure credential store.

Your computer must be awake, online, and logged in for background reminders. Incomplete Codex data or provider failures can prevent an alert.

## Installation and setup (preview)

This guide is for the **cross-platform development preview**. There is no finished installer or published release yet. Windows and Linux real-account and background-delivery tests were not performed; the project owner chose not to require them for this release. The app remains a prototype on every platform. If you would rather run the older macOS-only default branch, see [the default-branch instructions](#open-wuphf) below.

### 1. Install the prerequisites

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/) or your platform's package manager. On Windows, allow the installer to add Python to your PATH. On Linux, your distribution may also require its Python `venv` package.
2. Install the **Codex CLI** by following the [official Codex CLI guide](https://developers.openai.com/codex/cli/). Open Terminal, PowerShell, or a Linux terminal and run `codex`; sign in with the ChatGPT account whose banked resets you want to monitor. WUPHF uses the CLI's existing sign-in.
3. Confirm that `codex --version` works in the terminal where you will start WUPHF. If the command isn't found, follow the Codex guide's installation and PATH instructions and reopen your terminal.

**Linux only:** A graphical desktop session with a running systemd user service and an unlocked Secret Service keyring is required. The Windows and Linux launchers create a local Python environment and install WUPHF's open-source credential-storage dependency on first run, so an internet connection is needed.

### 2. Download and open WUPHF

1. [Download the cross-platform preview as a ZIP](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/heads/feature/cross-platform.zip), then extract it. This is source code from a development branch, not a signed installer.
2. Move the extracted folder to a location where it can stay; background checks use that folder. On macOS, keep WUPHF, its Python executable and the Codex CLI outside **Documents**, **Desktop**, and **Downloads**. For example, use `~/Library/Application Support/WUPHF`. The preview blocks background installation from those folders; other macOS privacy settings can still affect execution.
3. Open the folder and start the launcher for your computer:
   - **macOS:** Double-click `Start WUPHF.command`. If macOS blocks the unsigned launcher, open Terminal in the folder and run `python3 -m wuphf.web`.
   - **Windows:** Double-click `Start WUPHF.bat`. Keep the window open while using the setup page.
   - **Linux:** Open a terminal in the folder and run `./Start\ WUPHF.sh`.
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
- **Stop checks:** Click **Disable** under Background checks. This leaves your settings and credentials in place.
- **Remove local data:** After disabling checks, remove WUPHF's entries from macOS Keychain, Windows Credential Manager, or Linux Secret Service, then remove `~/.local/share/wuphf-resets/` (under your user profile on Windows). Remove an app-created Google calendar separately if desired.
- **Need help:** [Open an issue](https://github.com/Robertzu43/WUPHF-my-banked-resets/issues). Never include tokens, passwords, OAuth client files, raw auth files, or reset identifiers.

## Older macOS-only default branch

The following sections describe the older default branch, not the cross-platform preview above.

### Open WUPHF

These steps describe the **default-branch macOS prototype**. For the newer Windows, Linux, Gmail and pixel-interface preview, follow the [development branch setup guide](https://github.com/Robertzu43/WUPHF-my-banked-resets/tree/feature/cross-platform#try-the-prototype).

1. Install Python 3.11 or newer and the [Codex CLI](https://developers.openai.com/codex/cli/), sign in, and make sure `codex` is available in Terminal.
2. Keep the project in a background-accessible location such as `~/Library/Application Support/WUPHF`, outside Documents, Desktop and Downloads. In Finder, open `Start WUPHF.command`. Leave its Terminal window open while using the setup page.
3. Choose your notification channels, enter their details, and save. Send a test for each enabled channel.
4. To run checks in the background, choose **Enable checks**. The Mac must stay awake, online, and logged in. The project folder must stay in the same place.

If Finder blocks an unsigned download, open Terminal, change into the project folder, and run `python3 -m wuphf.web`. You need Python 3.11 or newer and the signed-in Codex CLI. Checks run approximately every 10 minutes, so shorter intervals cannot be guaranteed.

## Languages

Choose English, Spanish, German, Portuguese, French, Japanese, Korean, or Simplified Chinese in the setup page. Your choice is saved and applies to the interface, reminders, and calendar events. Translations are machine-assisted; contributions from native speakers are welcome.

## Notifications

The default branch includes legacy ntfy support. New release setup focuses on email and Telegram. Gmail and Telegram test messages were received on the developer’s Mac using the development version.

- **Telegram:** Create a bot using Telegram's @BotFather, start a conversation with it, and enter its bot token and chat ID.
- **Email:** Supply an SMTP SSL server, login, sender, recipient and an app password or other provider-compatible credential. The prototype supports SSL SMTP, typically port 465.
- **ntfy:** Supply an HTTPS server and topic. Public topics can be read by anyone who knows their name; use an authenticated topic for privacy.

Secrets are stored in macOS Keychain under `WUPHF My Resets`. A provider accepting a message is not proof that it reached your device. Each channel has a test button.

## Calendar

Download an `.ics` file for a one-time snapshot compatible with Google, Apple and Outlook calendars. Imported events do not update automatically.

To try automatic Google Calendar synchronization, WUPHF needs a registered **desktop OAuth client** in a Google Cloud project with the Google Calendar API enabled. In this prototype, download the client JSON from Google Cloud and select it once under Developer setup; do not paste its contents into chat. A distributor can instead include an appropriately registered `google-client.json` when packaging the app, so users can simply choose Connect Google. Complete Google's consent screen, then select **Sync now**. WUPHF requests permission for an app-created secondary calendar and creates or updates only its own reset events. It checks again with each background run. Because WUPHF cannot reliably detect every Codex account or workspace switch, it does not automatically delete calendar events: remove used or expired reset entries manually in Google Calendar. If your Google app is in testing mode, your account may need to be listed as a test user; Google authorization or verification requirements can apply. This integration has automated mock coverage but has not yet been tested with a live Google account. Your Google Calendar connection inside ChatGPT cannot be reused by the standalone app.

**Disconnect** removes local Google credentials and mappings; it does not delete the previously created Google calendar or its events. Remove that calendar separately in Google if desired. Reconnecting creates a new WUPHF calendar.

## Stop and uninstall

Use **Disable** on the setup page, or run `python3 -m wuphf.cli uninstall` from the project folder. This stops the background job but leaves settings and Keychain entries intact. Delete the `WUPHF My Resets` entries using Keychain Access and remove `~/.local/share/wuphf-resets/` if you want to remove local data. No Google calendar is deleted by uninstalling.

## Reliability and privacy

WUPHF uses the signed-in local Codex CLI and never redeems resets. If expiry details are missing, it shows them as unknown. The Mac cannot check or send alerts while asleep, off, disconnected, or logged out. Use your Mac power settings or `caffeinate` if you choose to keep it awake. Local state contains opaque credit identifiers for deduplication; do not share it or your Codex credentials.

## Versions and contributing

There is **no published release or version tag yet**. The planned first beta is a pre-release, such as `v0.1.0-beta.1`; development is tracked in the [release plan](https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/feature/cross-platform/docs/superpowers/plans/2026-11-07-public-beta-release.md).

Contributions and translation corrections are welcome. Open an [issue](https://github.com/Robertzu43/WUPHF-my-banked-resets/issues) without sharing credentials or private reset identifiers.

WUPHF is free and open source under the [MIT License](LICENSE). It is an independent project inspired by *The Office* and is not affiliated with OpenAI or the show.


## Tests and current limits

Run `python3 -m unittest discover -s tests -v` from this folder. The automated suite uses mocks for external providers and does not prove notification or calendar delivery. A live Codex read, a temporary macOS launch agent, and a temporary Keychain item were tested on the developer's Mac. Telegram, SMTP email, ntfy phone delivery and Google Calendar still need end-to-end tests with the user's own services. The separate Sign in with ChatGPT authorization did not provide account data through the tested configuration, so WUPHF uses your existing Codex CLI sign-in. Public distribution would need release signing, a simpler shared OAuth setup, and any applicable Google app verification.
