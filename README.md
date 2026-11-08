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
  <a href="#open-wuphf"><strong>Get started</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/tree/feature/cross-platform"><strong>Cross-platform preview</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/blob/feature/cross-platform/docs/superpowers/plans/2026-11-07-public-beta-release.md"><strong>Release plan</strong></a> ·
  <a href="https://github.com/Robertzu43/WUPHF-my-banked-resets/issues"><strong>Report an issue</strong></a>
</p>

> **Early prototype · No release published yet.** The default branch is the earlier macOS prototype. Windows, Linux, Gmail sign-in and the pixel interface are in the [cross-platform development branch](https://github.com/Robertzu43/WUPHF-my-banked-resets/tree/feature/cross-platform) and are not released. Google verification and real-device testing remain in progress. Keep a backup reminder until WUPHF is tested for your account.

WUPHF helps you track available Codex banked resets and remember known expiry dates. The planned release focuses on **email** and **Telegram**, with calendar export available. You choose when reminders start and how often they repeat. WUPHF never uses a reset for you.

## At a glance

- **Stay informed:** View available banked resets and known deadlines from your signed-in Codex CLI.
- **Choose your WUPHF:** Configure email, Telegram, or both, and send a test to each destination.
- **Save the date:** Export an `.ics` snapshot for compatible calendars; the preview also includes experimental Google Calendar sync.
- **Keep it local:** Your computer runs the checks and stores credentials in its secure credential store.

Your computer must be awake, online, and logged in for background reminders. Incomplete Codex data or provider failures can prevent an alert.

## Open WUPHF

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
