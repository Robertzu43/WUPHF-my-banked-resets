# WUPHF Calendar cleanup: conservative design decision

Read-only review, 2026-11-08. No repository changes, credentials, remote mutations, messages, jobs, or commits. Authoritative requirement: `docs/superpowers/specs/2026-11-08-product-quality.md`, outcome 6.

## Recommendation

Add cleanup for **new, explicitly marked, locally tracked, unchanged events** after a complete, semantically valid snapshot from the bound Codex account. Apply the same ownership/version checks before updating events. Preserve legacy events permanently unless the user manually removes them; do not add ownership markers to them. Use direct event GETs and the existing atomic mapping file and process lock. No list/sync-token service, remote sweep, database, or generic transaction layer is needed.

Prefer the small etag-based design below. Ordinary network/credential errors and interrupted deletion remain safely retryable. An insert/update that succeeded remotely but whose response or final local save was lost is an intentional **preserve-and-report** case, because the app cannot distinguish its own completed write from a subsequent user edit using the old etag alone. This is not full automatic recovery: if that stronger requirement is mandatory, use the narrowly scoped pending-intent alternative described below and budget the additional comparison tests. Do not describe the small version as covering every crash window automatically.

## Current evidence and reach

`wuphf/core.py:snapshot` checks count, row shape, unique nonempty IDs, and count/length agreement. Its `complete` value does not validate expiry or status. `valid_identity` accepts the expected 64-character SHA-256 fingerprint. `valid_expiry` excludes booleans, nonfinite values, negative values, and values beyond the date range with room for the one-minute event end. Leave these general snapshot semantics unchanged.

`wuphf/google.py:reconcile` checks complete/same-account, filters status to `available` (missing status defaults to available), skips individual invalid dates, calls `put`, and preserves every old event. `GoogleCalendar.put` GETs an arbitrary mapped ID then replaces any returned event, even an unmarked or cancelled one. Therefore adding only a deletion loop would leave a separate destructive-update defect. `request` currently conflates all 404 responses and some 410 responses with absence.

`wuphf/google_auth.py:sync` binds a fresh empty connection to its first stable Codex identity, rejects unknown/legacy connection binding or changed accounts, refreshes the token, creates the dedicated calendar if needed, and supplies the mapping persistence callback. `disconnect` removes local credentials/config/mapping only. Preserve these account/disconnect rules.

Callers are `wuphf/cli.py:main` (`run`) and `wuphf/web.py` (`/api/google/sync`). Both already acquire `storage.check_lock(DATA/'check.lock')`; web disconnect uses the same lock. `storage.save` writes a private temp file, flushes/fsyncs it, and atomically replaces the target. Do not add another lock or change notification-channel retry state.

Implementation reach: `wuphf/google.py`, `wuphf/google_auth.py`, `tests/test_google.py`; update CLI/web error tests only if reporting changes. Guide/Google production documentation must explain migration and preservation. Any new UI text must reach all eight languages and UI status tests. No exports or external Calendar library callers were found. Existing Google tests explicitly encode old-event retention, legacy mapped-ID updates, cancelled-event restoration, and recreation under the same ID; those expectations must change deliberately.

## Calendar-only input gate

Before any remote mutation, require:

1. `complete is True`, a nonnegative integer count excluding bool, a list of dictionary rows, unique nonempty string IDs, and exact count/length agreement. Revalidate at the Calendar boundary rather than trusting ad-hoc `complete=True` test fixtures.
2. A valid identity equal to the persisted connection fingerprint. Preserve existing identity-specific errors and check before token use or Calendar creation.
3. Every row has a valid expiry and `status` is absent or exactly `available`. An unfamiliar, null, malformed, or known-but-not-yet-supported status pauses Calendar reconciliation for the whole snapshot. Do not infer disappearance from the current filtered `active` dictionary.

Treat an empty, complete, same-account snapshot as valid: it can clean up eligible mapped events. One invalid date or unknown status anywhere pauses cleanup for all rows, including otherwise absent IDs. The simplest implementation pauses all Calendar writes for that snapshot; report a paused/failure result instead of a successful sync. `sync` should apply this gate before creating a calendar. A shared Calendar helper can be used by `sync` and `reconcile` without altering `core.snapshot`.

**Stale means absent from the full validated set of credit IDs.** No time-only cleanup and no inference that a strange status means redeemed.

An available credit with a valid past expiry remains present and is not deleted. Avoid creating new past events. For an existing trusted, unchanged event whose expiry moved into the past, update to that authoritative expiry under the same conditional-write rules, so a formerly future event does not keep the old future date. Do not promise cancellation of a popup already queued by a Calendar client. Capture `now` once per reconciliation (inject it in tests); do not make staleness depend on it.

## Minimal local/remote ownership contract

Keep the mapping keyed by credit ID. Legacy entries contain only `event_id` and `expiresAt` and remain untouched. A new managed entry additionally contains:

```json
{
  "event_id": "<random base32hex-compatible ID reserved before POST>",
  "expiresAt": 2000000000,
  "owner": "<random 128-bit or stronger hex token>",
  "account_fingerprint": "<bound fingerprint>",
  "calendar_id": "<bound calendar ID>",
  "etag": "<last successfully persisted remote etag>"
}
```

An entry without `etag` but with the other managed fields is a pending first insertion, never a legacy upgrade. Reserve its event ID and ownership token with `save_mapping` **before POST**. If that save fails, make no remote call. Random IDs stored before insertion allow a credit that disappears and later reappears to get a fresh event instead of resurrecting a cancelled Google ID. No raw credit ID or account ID goes into remote metadata.

On insertion only, include:

```json
{
  "extendedProperties": {
    "private": {
      "wuphfSchema": "1",
      "wuphfOwner": "<entry owner token>",
      "wuphfAccount": "<bound fingerprint>",
      "wuphfCredit": "<domain-separated SHA-256 of credit ID>"
    }
  }
}
```

Require the entry's account/calendar binding, GET response event ID, complete private marker, and saved etag all to match before any update or delete. Check exact marker values locally even if a future list filter is introduced. A title, description, dedicated calendar name, deterministic ID, creator field, or local mapping alone is insufficient ownership evidence. Malformed/duplicate local event IDs are ambiguous: preserve them and report instead of letting two entries act on the same resource.

Private metadata is useful ownership evidence, not an authentication boundary against another authorized Calendar writer deliberately copying it. A unique owner token and binding checks prevent accidental adoption; the saved etag prevents normal user edits/replacements from being silently accepted. Google makes these properties specific to a calendar/event copy; the metadata keys and values above fit its limits. [Google extended-properties documentation](https://developers.google.com/workspace/calendar/api/guides/extended-properties)

## Small concrete interfaces

Retain `reconcile(snap, mapping, api, save_mapping, *, account_fingerprint, now=None)` and its mapping return shape; production must supply the real persistence callback. Add `calendar_id` binding through `api.calendar_id` or a keyword, whichever keeps fakes clearest. Use a small Calendar gate shared with `sync`.

Replace blind `put(eid, expiry)` with explicit transport operations whose ownership policy stays in reconciliation:

```python
get(eid) -> event_dict               # or a typed not-found/deleted outcome
insert(eid, body) -> event_dict
update(eid, body, *, etag) -> event_dict
delete(eid, *, etag) -> None
request(method, path, payload=None, *, headers=None)
```

Use sanitized errors retaining status/reason internally, or a tiny exception carrying `status` and `reason`. Do not put URLs, provider response bodies, tokens, or IDs in user-facing errors. `request` must not turn every 404 into a successful missing event for every method. POST/PUT 404 is a failure. DELETE success is normally an empty response; reject malformed successful insert/update bodies that lack the expected ID, markers, and a nonempty etag.

`get` fetches by Calendar event ID, not iCalUID; it returns the event resource needed for ownership verification. [Events.get](https://developers.google.com/workspace/calendar/api/v3/reference/events/get)

For updates and deletes, send `If-Match` with the **persisted etag**, after confirming the fresh GET still has that etag. A 412 preserves local and remote state, reports the conflict, and must not trigger automatic adoption of the newer etag or unconditional retry. Google documents conditional updates and deletes, and insert uniqueness for a supplied ID. [Conditional modifications](https://developers.google.com/workspace/calendar/api/guides/version-resources)

## Reconciliation and retry rules

Process independent eligible entries and persist each confirmed change; never batch-drop mappings before remote success. Stop on a transport/persistence error with all unresolved work retained. Ownership/version conflicts may be accumulated and reported after other independently safe entries finish; alternatively fail early for the smallest implementation. Neither path should report a completely successful sync if a requested managed operation was blocked.

| Situation | Required action |
| --- | --- |
| Legacy entry, active or stale | Preserve mapping and remote event; no PUT, marker PATCH, or DELETE. Do not create a duplicate replacement for that mapped credit. |
| New future credit | Reserve mapping before POST; insert marked event; validate response and persist etag. |
| Insert timeout/409 or restart with pending reservation | GET only that reserved ID. If truly absent, retry the same POST/ID. If present with no saved etag, preserve/report ambiguity even when marker matches; do not silently adopt it. |
| Managed active event, markers and saved etag match | Skip unchanged payload; conditionally update only when required, then save returned etag/expiry. Keep markers in body. |
| Managed absent credit, markers and saved etag match | Conditional DELETE, then remove mapping and persist immediately. |
| Marker missing/wrong, response ID mismatch, no etag, saved etag mismatch, or malformed resource | Preserve remote and mapping; report. Never regenerate owner evidence from the returned event. |
| GET returns cancelled event | Do not restore it. For an active credit retain the mapping as a suppression record, preventing recreation on every poll. For an absent credit local tracking may be retired; no remote mutation is needed. |
| Credential failure, offline, 429/5xx, 412, unknown HTTP error | Keep unresolved mapping. Retry on a later scheduled/manual check; no immediate unbounded retry loop. |
| Successful DELETE followed by local save failure | Old mapping survives. Next valid snapshot GET may show cancelled/deleted: retire the local entry without another destructive call. If GET is ambiguous, retain and report. |
| Successful insert/update followed by lost response or local save failure | Preserve old/pending mapping. On retry GET/version mismatch exposes uncertainty; report instead of overwriting/deleting. This is the explicit small-design limitation. |
| Previously cleaned-up credit ID reappears | Allocate a new reserved event ID/token. Never restore an old tombstone or reuse its ownership. |

A 404 can mean missing resource **or inaccessible calendar**. Keep tracking and report on an ambiguous 404 from an existing mapping; do not forget it. Before retrying a pending first POST after 404, a successful direct `calendars.get` of the bound calendar can establish access; if this is omitted, POST still must be insert-only and its errors preserved, never treated as successful cleanup. A 410 is not universally “deleted”: inspect reason and endpoint. Recognized `deleted` for a direct event operation can be terminal; `fullSyncRequired`, unexpected reasons, or malformed error bodies are not. [Google Calendar error semantics](https://developers.google.com/workspace/calendar/api/guides/errors)

Cancelled nonrecurring events may expose only the ID and eventually disappear; they are not reliable persistent ownership records. Never restore a bare cancelled event merely because the local mapping contains its ID. [Event status semantics](https://developers.google.com/workspace/calendar/api/v3/reference/events)

Delete only unchanged app events with no attendees/recurrence/special event type. These should already be excluded by the etag check; also rejecting such shapes is inexpensive defense in depth. `DELETE .../events/{id}?sendUpdates=none` is supported by the current `calendar.app.created` scope; there is no need to broaden access. [Events.delete](https://developers.google.com/workspace/calendar/api/v3/reference/events/delete)

## Migration and honest reporting

Do not migrate unmarked events into managed ownership, including events whose content looks exactly like WUPHF's. Preserve their mappings so a future credit with the same ID does not create a duplicate. Continue existing disconnect/reconnect behavior: it preserves old calendars and creates a separate new bound calendar on a subsequent sync. Explain that old calendars/events can still remind until the user reviews/removes them in Google Calendar. Disconnect is not remote cleanup.

This first safe release cannot automatically fix stale reminders already present in the installed legacy population. That is a deliberate consequence of the requirement never to delete ambiguously owned legacy events, not a hidden complete migration. New events get lifecycle management; old ones remain manual. Document this limitation visibly near Calendar guidance, using existing localization and status mechanisms where possible. Do not add an automatic “adopt old events” control.

Keep account errors distinct. Data-invalid sync must be reported as paused rather than `True`; the CLI currently clears a Google failure for any complete snapshot, so if `False` is used for the new gate, adjust that clearing condition or raise a sanitized Calendar-specific error. A conflict must not claim that the user should reconnect as the only remedy, since reconnect preserves old events too. A small result/code or localized conflict message is preferable to broad reporting infrastructure.

## Alternatives and tradeoffs

**A. Recommended: saved etag with creation reservation, preserve/report uncertainty.** Smallest strong safety boundary; protects all user edits regardless of which field changed, with few new states. Offline/retry, ordinary restarts, failed deletes, and partial multi-event progress are straightforward. Cost: remote-success/local-save-loss can require manual Calendar review, and a benign provider etag change may conservatively stop management. Ownership conflicts are intentionally not self-healed.

**B. Pending operation record for automatic recovery.** Persist `{operation_nonce, expected_old_etag, desired_body}` before insert/update; embed the operation nonce with the remote private markers. After timeout/restart, accept the new etag only if the remote nonce is the pending nonce **and the entire relevant editable event state exactly matches the saved intended body**, with explicit default/date normalization and rejection of unexpected mutable fields. Otherwise preserve/report. Clear intent only after local save. Recheck current complete same-account snapshot before replaying any pending delete; old intent alone must not authorize deleting a credit that reappeared. This can recover an ordinary completed-write/save-loss case, but is materially more code and API-shape maintenance. Comparing only title/start/reminders or nonce is insufficient: a user may have added attendees, a description, recurrence, location, attachments, another private marker, or other content. Require focused recovery tests and independent review before choosing this option. A pending operation token alone does not prove that no later edit occurred.

**C. List marked events and sweep remote state.** Not needed for the default: reserving IDs before POST avoids untracked inserts in ordinary crashes, and direct GETs avoid paging. A remote sweep still cannot establish that a matching event was not user-edited if local etags are lost. If introduced later, follow every `nextPageToken`, including empty intermediate pages; never start cleanup from a partial/failed listing, and verify all ownership fields locally. The official extended-properties guide and list reference currently disagree about conjunction of repeated private-property filters, so do not rely on multiple filters as the safety predicate. [Events.list paging and filters](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)

**D. Delete by deterministic ID/title or silently mark legacy events.** Reject. Local files, event names, or IDs are not independent remote ownership proof. It also fails the explicit legacy-preservation requirement.

## Required tests before implementation approval

Use fakes with real event-shaped resources, markers, etags, cancelled tombstones, and per-call failure injection. Test outgoing urllib requests as well as reconciliation; a fake `put` accepting only a timestamp cannot prove ownership safety.

1. Complete zero same-account snapshot deletes only an unchanged newly managed stale event; unrelated and legacy events remain byte-for-byte untouched. Mapping disappears only after successful deletion.
2. Incomplete, count-unknown/mismatched, duplicate/malformed IDs, unknown identity, changed account, any invalid expiry (including bool/NaN/infinity/huge/negative), and unknown/null status cause no Calendar mutation. One bad row blocks cleanup of a different absent row. Missing status retains the existing available convention.
3. Present ID is never considered stale because a status filter excluded it. Valid past date does not authorize deletion; new past credits are skipped and trusted existing future events can be moved to the past. Boundaries are deterministic with injected time.
4. New insertion includes correct private markers; reservation persists before POST. Pre-POST save failure causes zero remote writes. POST conflict never falls through to PUT or silently allocates repeated duplicate IDs.
5. Updates and deletes require both exact markers and saved etag. Independently vary owner/account/credit/schema/event ID/calendar binding, local-entry shape, duplicate mapping IDs, and absent etag. Every mismatch preserves the remote event.
6. User edits to title/date/reminders/description, added attendee/recurrence, replaced-ID resource, and removed markers cause no update/delete. Race after GET yields request with If-Match and a 412; no unconditional retry or saved-etag adoption.
7. Cancelled event with only an ID is never restored. Active cancelled mapping suppresses recreation across restart; absent cancelled entry can retire locally. A later same credit after successful stale cleanup receives a fresh ID.
8. Token/offline/429/5xx/GET failures preserve state and recover after restart. Successful first event followed by second-event failure retains first persisted progress. Corrupt mapping/config raises without remote writes.
9. Delete success plus save failure recovers on cancelled/explicitly deleted response. Ambiguous 404/access loss and unrelated 410 reasons retain mapping; empty successful DELETE is accepted. Insert/update malformed success body is not silently trusted.
10. Lost insert/update response or final save produces preserved ambiguous state and a visible non-success result under option A. No automatic etag adoption. If B is chosen, additionally test every pending state and post-write user edit, including extra editable fields and equivalent RFC3339 offsets.
11. Legacy mappings receive neither markers nor updates/deletes; existing unbound-connection rejection and disconnect preservation remain. CLI/web reflect invalid-data/conflict outcomes truthfully and scrub provider secrets.

Run the focused Google/CLI/web/storage/core tests, then the repository's existing broader release checks after the chosen implementation. This document did not execute tests because no code changed.

## Remaining uncertainties / release limits

No live provider validation was performed. Google documents etag conditional DELETE support, but candidate code still needs transport tests; personal live credentials are outside this design task. A deleted event's tombstone may omit metadata, so cleanup recovery must never depend on its marker surviving.

Option A does not automatically recover the success-before-local-save crash window for insert/update. That explicit manual-review path is the recommended safety/complexity tradeoff. If the product acceptance bar requires fully automatic recovery there, choose and test B before calling the reliability gap complete.

Legacy and user-edited events can continue reminding. Local state deletion or user reconnect can leave old remote calendars/events. No safe automatic algorithm can infer ownership/version history that was never recorded; do not hide this limit behind a success message.


## Orchestrator decision for implementation

Selected alternative A under the existing user authorization to resolve reliability/usability gaps. Remote-success/local-save-loss remains a visible preserve-and-review conflict, never a reason to adopt a newer etag. This prioritizes existing user data and a small auditable implementation over an unproved transaction framework. No real account cleanup is authorized by automated QA. Legacy calendars/events remain manual; new owned events receive lifecycle management. The broader quality goal is not complete merely because this task passes.

Use `CalendarSyncError(RuntimeError)` with a sanitized `.code` and `CalendarAccountError(CalendarSyncError)` retaining its current codes. New codes: `calendar_data_required` (refresh complete valid reset details), `calendar_event_conflict` (review unchanged/legacy/edited Calendar events; no automatic adoption). CLI should store only sanitized messages; web returns the code and all eight catalogs/serverErrors map it. Scope is the current connection's local mapping and dedicated calendar, with no remote sweep.
