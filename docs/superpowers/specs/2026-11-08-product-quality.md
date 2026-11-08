# WUPHF product quality target

User authorization: improve all dimensions of the independent usability review using development/QA subagents, orchestrated implementation, re-review, merge and publish. Existing approved pixel design, independent local installations and optional Gmail/SMTP/Telegram/ICS/Google Calendar remain the product foundation.

## Design decision
Improve the existing Python/vanilla-browser app rather than rewrite it or introduce a hosted account service. A rewrite adds migration risk; hosted reminders change the user's local/free/privacy requirements. Preserve the current visual identity while making the current workflows self-explanatory. This is the orchestrator's implementation choice under the user's execute-and-publish authorization.

## Required outcomes
1. Purpose: define banked resets as saved one-time resets expiring at known dates; distinguish regular allowance refresh, explain manual redemption and link authoritative help.
2. Setup: make select → save → test → enable discoverable beside actions; visibly mark unsaved settings; prevent tests of stale settings. Disable or explain disconnected/inapplicable actions, recover after errors and never imply provider acceptance proves receipt.
3. Daily use: show unambiguous expiry with timezone, data freshness, and background health; show truthful provider-test status; avoid invented delivery guarantees. Account/incomplete-data limitations remain visible but understandable.
4. Help: local UI links the full guide, import instructions and provider restrictions at the point of use. SMTP is explicitly SSL only and distinct from Gmail. BotFather is actionable and manual chat ID is explained as fallback.
5. Installation: complete packages with convenient launchers, checksum verification, permanent location, diagnostic/recovery path and upgrade/uninstall instructions. No global security disable, paid purchase, secret publication or unsafe credential handling. Signed/notarized distribution requires actual signing resources and successful platform verification, not renamed files.
6. Reliability: preserve per-channel retry/deduplication and conservative handling of unknown balances/identity. Calendar cleanup must never delete unrelated or ambiguously owned events. Test offline/recovery, account change, credential failures and restart scenarios before changing their semantics.
7. Eight UI languages, keyboard access and reduced motion remain supported; new copy must be localized.
8. Release: new version for changed binaries, CI/test/build/artifact checks, independent code and browser QA, updated guide/evidence/changelog, merged PR, immutable prior beta preserved.

## Evidence and scoring
A fresh independent reviewer re-scores purpose, installation, onboarding, daily use, docs and overall usability against actual delivered UI. A 10/10 claim requires first-time-user task evidence and no material unresolved friction, not a forced reviewer score. Record gaps honestly and keep this goal active when any requirement is unproved. Respect the owner's existing Windows/Linux real-device waiver; it does not establish device testing. No use of personal credentials or live sends during automated QA.

## Orchestration
Root owns scope, integration, evidence ledger and release decisions. Development tasks have explicit file ownership. Fresh QA reviewers inspect each task before integration. Re-review failures go to the original implementer; whole-branch review follows passing task reviews. External provider/signing decisions are recorded without substituting prose for working integration.
