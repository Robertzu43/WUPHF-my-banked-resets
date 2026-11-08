# Google setup for maintainers

Normal users select **Connect Gmail** or **Connect Google** in WUPHF without creating a Google Cloud project. Both APIs are enabled for WUPHF's registered Desktop client. Google verification is pending, and live Calendar sync has not yet been verified.

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

On November 7, 2026, Google Cloud showed WUPHF's audience as **External / In production**, with verification still required and a **100-user unverified OAuth cap**. Production status is not Google's approval.

The branding issue reported that the homepage ownership was not yet recognized. Search Console ownership was completed earlier that day; Google's dialog explicitly asks maintainers to wait **24 hours** after ownership verification before retrying. The public homepage and privacy policy are deployed under `https://robertzu43.github.io/WUPHF-my-banked-resets/` and the privacy policy is linked from the local app.

1. After the ownership propagation period, return to Google Auth Platform **Branding → View issues**, retry the ownership check and submit branding for review when eligible.
2. After branding is accepted, complete **Verification Center** requirements for the scopes actually requested. Provide the app description, scope justification, public privacy policy and any demonstration Google requests. Do not request broader permissions to avoid a review.
3. Test the complete production browser flow on the same computer as WUPHF, then test sending and later token refresh. Old callback URLs expire; always start a fresh connection in the app.
4. Update the README and app disclosure only after Google reports approval. Until then, keep the unverified/experimental limitation visible; users can choose Telegram.

Google's console is the authority for current review status. A successful mocked test, bundled registration, or production toggle cannot establish verification or permanent authorization.
