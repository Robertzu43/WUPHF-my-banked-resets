<p align="center"><img src="docs/images/wuphf-logo.svg" width="128" alt="WUPHF pixel logo"></p>

# WUPHF! for Codex Banked Resets

**Your reset bank called. It wants you to use it.**

WUPHF helps you keep track of available Codex banked resets and reminds you before known expiry dates. Pick the channels you want: Gmail or other email, Telegram, ntfy, and calendar events. WUPHF never uses a reset on your behalf.

> **Status: early prototype.** There is no published release yet. This branch adds Windows and Linux support and is still under review. Live setup and background delivery have not been fully verified on every platform or for every channel. Keep a backup reminder until they have been tested for your account.

[Release plan](docs/superpowers/plans/2026-11-07-public-beta-release.md) · [Report an issue](https://github.com/Robertzu43/WUPHF-my-banked-resets/issues) · [License](LICENSE)

## What you can do

- See your available banked reset count and known expiry dates using your existing Codex CLI sign-in.
- Choose when reminders start and how often they repeat. Use any combination of supported channels.
- Export an `.ics` snapshot for Google Calendar, Apple Calendar, Outlook, and other compatible calendars. Experimental Google Calendar sync can add events to a separate WUPHF calendar.
- Use English, Spanish, German, Portuguese, French, Japanese, Korean, or Simplified Chinese. Translations are machine-assisted.

WUPHF runs locally. Your computer must be awake, online, and logged in for background checks and messages to run. Unknown or incomplete Codex data cannot be treated as a confirmed expiry or a used reset. Delivery depends on your selected services.

## Try the prototype

These instructions describe the current **cross-platform development branch**, not a finished installer. Windows and Linux require full real-account testing before release.

1. Install **Python 3.11 or newer** and the [Codex CLI](https://developers.openai.com/codex/cli/). Sign in to the CLI with the ChatGPT account whose resets you want to track.
2. Download and unzip the [`feature/cross-platform` branch](https://github.com/Robertzu43/WUPHF-my-banked-resets/archive/refs/heads/feature/cross-platform.zip). Keep the extracted folder in a permanent location: background checks need it to remain there.
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
2. The prototype currently needs a Google desktop OAuth client with the Gmail API enabled. Select its JSON file under **Developer setup** if one is not already provided locally. This file stays on your computer.
3. Click **Connect Gmail**, approve Google's send-only permission if you agree, and return to WUPHF. Save settings, send a test, and check your inbox.

Google may require app verification or restrict who can authorize a client. An app-owned, verified client for a simpler public connection is planned; don't assume this is finished. A Gmail connection in Codex or ChatGPT cannot be reused by this standalone app. A test email was received on the developer's Mac; background delivery and broader account coverage still need validation.

### Other email

Enable **Email** and enter your provider's SMTP SSL server and port, username, sender, recipient, and provider-compatible password or app password. Save and send a test. Provider requirements vary; the prototype supports SMTP over SSL, typically port 465.

### Telegram

1. In Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, and follow its prompts to create your own bot. Keep the resulting bot token private.
2. Open your bot, press **Start**, and send it a message. Enable Telegram in WUPHF and paste the token.
3. Click **Find my chat ID**, check that the displayed private chat ID is yours, and click **Save settings**. Then send a test. You can enter the ID manually instead.

The optional lookup checks pending updates only when you click the button and does not confirm those updates. If multiple private chats or too many updates are pending, or a webhook or another bot client prevents polling, enter your private chat ID manually. Telegram was tested on the developer's Mac; broader delivery testing is still needed.

### ntfy

1. Install an ntfy client on your device. Enable **ntfy push** in WUPHF and enter your HTTPS server (the default is `https://ntfy.sh`).
2. Click **Generate a topic** or enter your own. Subscribe to the same topic in the ntfy app. If your server uses an access token, enter it in WUPHF too.
3. Save settings and send a test. Confirm it arrives on your device.

Anyone who knows an unprotected topic can read its notifications. A random topic name is not access control: use an authenticated topic for privacy. Live phone delivery still needs testing.

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
