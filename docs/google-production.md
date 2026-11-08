# Google setup for maintainers

Each user runs WUPHF on their own computer and connects their own Google account. Normal setup uses **Connect Gmail** or **Connect Google** without creating a Google Cloud project: both APIs are enabled for WUPHF's bundled Desktop registration. This registration identifies the app; it does not share the developer's account, tokens or calendar with users. An own-client override is available below.

The owner authorized publishing the beta with all existing options. Google verification remains pending and is a disclosed integration limitation, not a prerequisite for publishing this code or beta. The bundled registration remains subject to Google's unverified-app warnings, account restrictions and 100-user cap; unlimited public Gmail onboarding is not claimed.

## Registration and local credentials

`wuphf/oauth-client.json` contains only WUPHF's registered **Desktop app** client ID and client-secret parameter. Desktop applications are public OAuth clients: their embedded registration parameters cannot be kept confidential. They are not a user's access token, refresh token, password, or Google account. See [Google's installed-app OAuth documentation](https://developers.google.com/identity/protocols/oauth2/native-app).

The owner approved public distribution of this Desktop registration. The repository secret scanner retains its default rules and has one exception requiring both this exact file path and the exact public parameter value; different values or files remain scanned.

WUPHF uses the system browser, a loopback callback, a random state value and PKCE. Individual user refresh tokens stay in the operating system credential store. Builds whitelist the public registration fields and reject personal OAuth/configuration files. Never substitute a web application's confidential server credentials or include user tokens in this file.

For a fork or an optional personal registration, create a Desktop app client in your own Google project, enable the relevant APIs, and configure its consent screen. Select the downloaded JSON in **Developer setup** before connecting. A local root `google-client.json` also overrides the distributed registration for source installations; it is ignored by Git and excluded from packages. Existing connections retain their original client until disconnected and reconnected.

## Requested permissions

| Integration | Scope | Purpose |
| --- | --- | --- |
| Gmail | `https://www.googleapis.com/auth/gmail.send` | Send the user's reminder and test messages. No inbox reading. |
| Google Calendar | `https://www.googleapis.com/auth/calendar.app.created` | Create a separate WUPHF calendar and manage its expiry events. No access to unrelated calendars is requested. |

The two connections are independent. Disconnecting removes local authorization; it does not delete previously created Google calendars or revoke an app grant on Google's account page. Google can expire or revoke tokens even after an app enters production.

## Verification status and next steps

The November 7–8, 2026 Google Cloud inspections showed WUPHF's audience as **External / In production**, with verification still required and a **100-user unverified OAuth cap**. Production status is not Google's approval. Data Access declares Gmail send-only as sensitive and Calendar app-created as non-sensitive, with no restricted scopes. The Gmail justification is saved; the required demonstration video URL remains outstanding.

Branding still reported that homepage ownership was not recognized at the November 8, 00:14 Bogotá check, less than 24 hours after the November 7 Search Console verification by the same account; Google's dialog explicitly asks maintainers to wait **24 hours** after ownership verification before retrying. The public homepage and privacy policy are deployed under `https://robertzu43.github.io/WUPHF-my-banked-resets/` and the privacy policy is linked from the local app.

1. After the ownership propagation period, return to Google Auth Platform **Branding → View issues**, retry the ownership check and submit branding for review when eligible.
2. After branding is accepted, complete **Verification Center** requirements for the scopes actually requested. Provide the app description, scope justification, public privacy policy and any demonstration Google requests. Do not request broader permissions to avoid a review.
3. Record the actual consent and integration workflows for the verification submission. Continue packaged Calendar UI, disconnect/reconnect and later unattended-refresh checks; the completed live evidence below does not establish those paths. Old callback URLs expire; always start a fresh connection in the app.
4. Remove the pending-verification disclosure only after Google reports approval. Until then, retain warnings and account limits while offering Gmail, Calendar and the other existing beta options.

Google's console is the authority for current review status. A successful mocked test, bundled registration, or production toggle cannot establish verification or permanent authorization.

## Completed live evidence and limits

The saved Gmail authorization refreshed successfully. Fresh Gmail and Telegram test messages were accepted by their providers; earlier device receipt was confirmed by the user. Provider acceptance alone does not prove new device receipt.

After explicit owner consent, Calendar authorization was saved in the OS credential store. A separate process using candidate `472ebcc` source helpers refreshed that saved token, created a WUPHF secondary calendar, created a labeled synthetic event, updated the same event by one hour and read back its expected ID, title and time with notifications disabled. The event was also verified in Google Calendar's UI. The test event is retained and the saved calendar ID enables normal background sync.

This verifies the source helpers and current saved-token refresh against live APIs. It does not verify the packaged Calendar browser UI, disconnect/reconnect lifecycle or later unattended refresh. Calendar imports into other applications remain untested. Credentials are local to each user's installation; no developer account token or live test data is distributed in the packages.
