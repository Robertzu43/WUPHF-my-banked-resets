# WUPHF! for Codex Banked Resets

Inspired by WUPHF from *The Office*, WUPHF! for Codex Banked Resets tracks your saved Codex resets and reminds you before they expire through the channels you choose. This is an **early desktop prototype**, not a finished release; don't rely on it as your only reminder until the notification and calendar connections have been tested on your account.

## Open WUPHF

Install Python 3.11 or newer and the Codex CLI, then sign in to the CLI. Download the project and open the launcher for your computer:

- **macOS:** Open `Start WUPHF.command` in Finder.
- **Windows:** Double-click `Start WUPHF.bat`.
- **Linux:** Run `./Start WUPHF.sh` from the project folder. A graphical desktop session with the Secret Service credential store and systemd user services is required.

The Windows and Linux launchers create a local Python environment and install the open-source `keyring` package on first run. Linux may also require your distribution's Python `venv` package and an unlocked desktop keyring. If the launcher cannot find Python or Codex, install them and reopen your terminal or session.

In the setup page, choose the channels you want, save their settings, and send a test for each. Select **Enable checks** to run in the background. Your computer must remain awake, online and logged in, and the project folder must stay in the same place. Checks run approximately every 10 minutes.

If macOS blocks the unsigned launcher, open Terminal in the project folder and run `python3 -m wuphf.web`. This is a prototype: Windows and Linux need native end-to-end testing before a public release.

## Languages

Choose English, Spanish, German, Portuguese, French, Japanese, Korean, or Simplified Chinese in the setup page. Your choice is saved and applies to the interface, reminders, and calendar events. Translations are machine-assisted; contributions from native speakers are welcome.

## Notifications

- **Telegram:** Create a bot using Telegram's @BotFather, start a conversation with it, and enter its bot token and chat ID.
- **Gmail (experimental):** Choose Gmail, enter the same Gmail address you will authorize, then select **Connect Gmail** and save your settings. This uses Google’s send-only Gmail permission and stores the refresh token in your computer’s secure credential store. A registered Google desktop OAuth client with the Gmail API enabled must currently be supplied under Developer setup; a public release needs an app-owned client and may require Google verification. The connected Gmail account in Codex cannot be reused by this standalone app. The connection has automated mock coverage but has not been tested with a live Gmail account.
- **Other email (SMTP):** Supply an SMTP SSL server, login, sender, recipient and an app password or other provider-compatible credential. The prototype supports SSL SMTP, typically port 465.
- **ntfy:** Supply an HTTPS server and topic. Public topics can be read by anyone who knows their name; use an authenticated topic for privacy.

Secrets are stored in the operating system’s credential store under `WUPHF My Resets`: Keychain on macOS, Windows Credential Manager on Windows, or Secret Service on Linux. WUPHF refuses insecure plaintext keyring backends. A provider accepting a message is not proof that it reached your device. Each channel has a test button.

## Calendar

Download an `.ics` file for a one-time snapshot compatible with Google, Apple and Outlook calendars. Imported events do not update automatically.

To try automatic Google Calendar synchronization, WUPHF needs a registered **desktop OAuth client** in a Google Cloud project with the Google Calendar API enabled. In this prototype, download the client JSON from Google Cloud and select it once under Developer setup; do not paste its contents into chat. A distributor can instead include an appropriately registered `google-client.json` when packaging the app, so users can simply choose Connect Google. Complete Google's consent screen, then select **Sync now**. WUPHF requests permission for an app-created secondary calendar and creates or updates only its own reset events. It checks again with each background run. Because WUPHF cannot reliably detect every Codex account or workspace switch, it does not automatically delete calendar events: remove used or expired reset entries manually in Google Calendar. If your Google app is in testing mode, your account may need to be listed as a test user; Google authorization or verification requirements can apply. This integration has automated mock coverage but has not yet been tested with a live Google account. Your Google Calendar connection inside ChatGPT cannot be reused by the standalone app.

**Disconnect** removes local Google credentials and mappings; it does not delete the previously created Google calendar or its events. Remove that calendar separately in Google if desired. Reconnecting creates a new WUPHF calendar.

## Stop and uninstall

Select **Disable** in the setup page, or run `python -m wuphf.cli uninstall` using the same Python environment as the launcher. This stops the background job but leaves settings and credentials intact. Remove the `WUPHF My Resets` credentials from your OS credential manager and delete `~/.local/share/wuphf-resets/` (on Windows, this is under your user profile) to remove local data. Google calendars are not deleted automatically.

## Reliability and privacy

WUPHF uses the signed-in local Codex CLI and never redeems resets. If expiry details are missing, it shows them as unknown. Your computer cannot check or send alerts while asleep, off, disconnected, or logged out. Adjust power settings if you choose to keep it awake. Local state contains opaque credit identifiers for deduplication; do not share it or your Codex credentials.

## Tests and current limits

Run `python3 -m unittest discover -s tests -v` from this folder. The automated suite uses mocks for external providers and does not prove notification or calendar delivery. A live Codex read, a temporary macOS launch agent, and a temporary Keychain item were tested on the developer's Mac. Telegram, Gmail, SMTP email, ntfy phone delivery and Google Calendar still need end-to-end tests with the user's own services. The separate Sign in with ChatGPT authorization did not provide account data through the tested configuration, so WUPHF uses your existing Codex CLI sign-in. Windows and Linux have automated coverage but require native end-to-end validation. Public distribution would need platform packaging and signing, a simpler shared OAuth setup, and any applicable Google app verification.
