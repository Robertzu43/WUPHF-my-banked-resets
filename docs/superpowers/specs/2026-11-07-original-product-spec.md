> Historical approved spec: the later release plan supersedes macOS-only scope and updates the evidence for live tests.

# WUPHF My Resets — product and technical specification

Status: draft for review · 7 November 2026

## Purpose

Help Codex users notice and use their available banked rate-limit resets before expiration. WUPHF is a free, open-source, locally running macOS application. Setup should be as simple as practical. Users select any combination of Telegram, email, ntfy and calendar; they control when and how frequently reminders are sent. A reset is always redeemed by the user, never by WUPHF.

## Approaches considered

1. **Local background application (selected):** Runs on the user's own Mac using their Codex account. No central service is needed, but the computer must be awake, online, and the user logged in.
2. **User-owned always-on server:** Works when a laptop is off but requires another machine and remote setup. Consider later.
3. **Codex Cloud:** Tasks can run while a computer sleeps, but persistent scheduling, durable state and appropriate account access for this application have not been established. Do not depend on it in v1.

## User experience and scope

- Provide a guided installation, clear prerequisites and a way to uninstall. Target macOS first. Do not claim a particular installer or one-click experience until packaging and distribution are tested.
- Guide the user through an authorized ChatGPT/Codex sign-in. Prefer the requested Sign in with ChatGPT integration **only if** a hands-on test confirms that its authorization can read the user's banked reset details. The proven fallback is the locally installed and signed-in Codex CLI using the supported app-server interface; explain that dependency and account selection clearly. Do not silently switch accounts.
- Show available count, known expiry times in the user's local time zone, last successful check, monitoring status and enabled notification channels. Offer an immediate refresh and indicate missing or stale data.
- Users enable any combination of Telegram, email, ntfy and calendar, including calendar alone; each messaging channel has a test action and visible success or failure. Setup explains provider-specific prerequisites without requesting credentials until needed.
- Let users configure an advance warning threshold and repeat interval. Suggested initial defaults: 7 days before expiry and daily repeats. They may change either or disable reminders. When the app starts after a missed interval and the reset is still known to be available, send at most one current reminder per channel, then resume the schedule. Do not send old reminders in a burst.
- Provide an optional Google Calendar connection that creates and maintains WUPHF events, and an `.ics` export for compatible calendars. The exported file is a one-time snapshot; it will not update an imported event. Automatically updating Google Calendar requires an authorized Google account, an API client and any applicable Google app verification before public distribution.
- Notify when a newly observed banked reset appears, and remind while it is unused and nearing its known expiration. Present status without claiming a disappearance proves redemption; a credit may have expired, become unavailable, or be absent due to incomplete upstream data.

## Reset data and tracking

- Use `codex app-server` over stdio, initialize the connection, and call `account/rateLimits/read`. No model prompt or reset-consume operation is required. Display `rateLimitResetCredits.availableCount` as the authoritative available count when provided.
- Track individual returned credits using their opaque IDs locally, storing only the minimum state needed for monitoring and deduplication. Use returned expiry timestamps, never an inferred universal expiry period.
- Treat `rateLimitResetCredits: null`, missing detail lists, absent expiry values, auth errors and network failures as **unknown**, not zero. Detail rows may be capped. If count exceeds detail rows, show incomplete details and do not assume omitted credits were used or expired. Never fabricate an expiry or send an expiry-specific reminder without an expiry.
- A complete snapshot has a valid nonnegative count and a non-null list of uniquely identified credits whose length equals that count. A null list remains unknown even when the count is zero. Only compare two complete snapshots to detect new or missing credits. The first complete read, and recovery without a complete prior snapshot, establishes a baseline; existing credits are still eligible for expiry reminders. Notify about newly observed credits only when comparing complete snapshots.
- For Google Calendar, create/update an event only for a known available credit with an expiry. Remove or mark a WUPHF-owned event as no longer current only after a complete, successful read establishes the credit is no longer available; retain and mark stale on unknown or incomplete reads. Never edit unrelated calendar events. WUPHF owns the events it creates: it may update their expiry-related fields and remove them when a complete read confirms the credit is no longer available; explain this before connecting. If a user deletes an event, recreate it on a subsequent complete sync while the associated credit remains available. Persist event mappings to avoid duplicates; use stable IDs or equivalent idempotency. Do not claim a disappeared credit was redeemed.
- If a reset has expired before monitoring resumes, show that the last known deadline passed; do not claim it remained unused throughout the gap. If a provider was unavailable, retry with bounded backoff and show the failure. Track each channel's delivery state separately and do not record successful delivery merely because a request was attempted. Provider acceptance is not a guarantee of receipt. A crash after provider acceptance but before recording success can cause a duplicate on retry; exactly-once delivery is not promised.

## Channels and credentials

- **Telegram:** User creates or supplies their own bot, starts a chat with it, and supplies/authorizes the chat destination; guided setup should reduce friction. Keep bot credentials secret. Avoid shipping a shared bot token in a public client.
- **Email:** User supplies an SMTP provider and appropriate credentials or another supported secure sign-in. Use TLS, local secret storage, and a test message. Provider eligibility, authentication and sending limits vary; no universal free email delivery is guaranteed.
- **ntfy:** Support public or user-hosted server, topic, and optional access token. Explain that unprotected topics can be read by others; generate an unguessable topic and recommend access control for private use. Send minimal reset information.
- **Google Calendar:** Use Google OAuth with the narrowest scope that supports the chosen calendar and event operations. `calendar.app.created` may allow a dedicated app-created calendar; verify the whole create/update/delete flow before committing to a scope. Public OAuth verification and Google Cloud project setup are release prerequisites where applicable, not assumed complete.
- Store tokens and passwords in macOS Keychain where feasible. Never log secrets, raw auth files, access tokens or credit IDs. No centralized account database or telemetry is required for v1.

## Background operation and reliability

- Use a user-level macOS background mechanism, configured only with the user's consent, that starts at login and can be disabled/uninstalled. The app checks periodically and on startup/wake, with reasonable bounded retry and jitter. Define the exact check interval during implementation; it must support the user's chosen reminder frequency without needless polling.
- Explain that monitoring cannot run while the Mac sleeps, is off, or the user is logged out; without internet it cannot refresh account data or send notifications. Keychain access may also require an unlocked user session. Offer optional instructions for keeping a Mac awake, including `caffeinate`; do not change power settings without consent. Avoid guarantees of delivery.
- Present last successful check, errors, stale state and disabled channels clearly. An unreachable app cannot itself guarantee an immediate failure alert.

## Verification and acceptance criteria

1. On an authenticated Codex account, retrieve count and available detail rows, and show timestamps correctly in the user's time zone. Compare results with the Codex usage interface.
2. Unit-test baseline, new credit, changed expiry, removal after a complete response, null/missing count/details/expiry, capped rows, errors, and stale state. Test that uncertainty cannot erase an event or trigger a false claim.
3. Test configurable warning and repeat cadence, startup/wake catch-up, per-channel deduplication, failure/retry, restart persistence and time-zone changes with a controllable clock.
4. With test accounts or local mock servers, verify Telegram, email and ntfy setup, test messages, failed delivery and secret handling. Separately confirm actual provider receipt with user-authorized test destinations.
5. Verify Google OAuth and dedicated calendar permissions, idempotent event creation/update/removal, access revocation and unavailability. Test `.ics` import and explicitly verify snapshot semantics. External-service tests require accounts and credentials.
6. Verify install, background start, logout, sleep/wake, uninstall and macOS secret storage on supported macOS versions. Security-review distribution, dependencies and any reused source code licenses.
7. Never invoke `account/rateLimitResetCredit/consume` in monitoring or tests. No external messages or calendar events are sent without the user's configured authorization.

## Evidence and current limits

- **Live tested on 7 November 2026:** Codex CLI 0.165.0 using the user's existing local Codex sign-in returned two available credit rows with expiry timestamps. Three repeated reads over 20 seconds were stable. Synthetic tracking checks exercised unchanged, changed and missing/incomplete data; no actual reset was consumed or changed during the test.
- **Documented:** [Codex App Server rate limits](https://learn.chatgpt.com/docs/app-server) provides available counts and optionally per-credit details; counts and rows can be incomplete. [Sign in with ChatGPT for app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server) documents OAuth-backed inference, but does not establish that this token flow can read banked-reset details. The app-server's externally managed ChatGPT token login is experimental. Test compatibility; do not treat it as confirmed.
- **Documented:** [Telegram bot tutorial](https://core.telegram.org/bots/tutorial) requires a user to contact the bot before it can send a private message. [ntfy](https://docs.ntfy.sh/publish/) supports publishing and access control. [Google Calendar scopes](https://developers.google.com/workspace/calendar/api/auth) and [event updates](https://developers.google.com/workspace/calendar/api/v3/reference/events/update) establish API capability, not completed authorization or public release approval.
- **Documented:** Apple describes [per-user launch agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html); actual packaging, macOS versions, sleep and restart behavior remain to be tested.
- **Not yet tested:** separate Sign in with ChatGPT integration; real changes to a reset; actual Telegram, SMTP, ntfy or calendar delivery; Google OAuth verification; installation; background persistence; provider costs and limits for individual users. Free software does not guarantee third-party services or connectivity are always free or available.

## Non-goals

Automatic redemption, paid messaging services, hosting a central multi-user service, predicting promotional resets, Windows/Linux support in the first release, and a guarantee of uninterrupted delivery are outside v1.
