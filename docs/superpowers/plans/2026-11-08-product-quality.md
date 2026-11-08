# WUPHF Product Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every evidenced usability gap, verify independently and publish the improved product while maintaining truthful quality gates.

**Architecture:** Retain the local Python server and vanilla browser UI. Add derived setup/readiness state without changing secret storage or reminder delivery semantics. Improve launch/distribution separately, then integrate and review the whole product.

**Tech Stack:** Python 3.11+, standard library, existing OS keyring, vanilla JavaScript/CSS, Node behavioral tests, PyInstaller, GitHub Actions.

**Spec:** docs/superpowers/specs/2026-11-08-product-quality.md

## Global Constraints
- Existing approved pixel design and eight languages are preserved.
- Channels remain optional and use the installer's own accounts.
- No global security bypass, paid purchase, secret disclosure or real messages during QA.
- Prior v0.1.0-beta.1 assets/tag remain immutable; runtime releases require a new version.
- Unknown data and provider acceptance must never be presented as confirmed balance/delivery.

## Review Focus
- Editing a saved channel before testing must not test stale destinations or secrets (Task 1).
- Failed save/test/auth must recover without incorrectly showing readiness (Tasks 1–2).
- Missing dates/identity and stale snapshots must not look current or empty (Task 1).
- Relocation, spaces in paths and repeated install/upgrade must preserve data and jobs (Task 3).
- Provider unavailability/restart must retain retry and duplicate protection (Task 4).

### Task 1: Guided setup and purpose in the actual UI
Files: wuphf/web.html, wuphf/translations.json, tests/test_setup_ui.js, existing UI tests as necessary.
Consumes existing settings/status/provider/background APIs. Produces derived dirty/readiness state in browser; provider acceptance is labeled test accepted, not received.
- [x] Add failing behavioral tests for edit→save→test ordering, initial loading, failed save, disconnected controls and zero/incomplete state.
- [x] Implement localized banked-reset definition/manual-use guidance and guide/import links, explicit Gmail/SMTP/Calendar labels and inline Google restrictions.
- [x] Implement dirty state, adjacent sequencing/checklist, applicable provider action states, honest test result/receipt distinction, explicit timezone/freshness and actionable BotFather/manual-chat instructions. ICS-only users must not be forced into background checks.
- [x] Run Node UI checks and Python i18n/web tests; fix failures; commit only task files.
- [x] Fresh reviewer checks task against spec and actual tests; fix and re-review.

### Task 2: Persist truthful test/check evidence
Files: wuphf/web.py, tests/test_web.py; minimal shared helper if needed.
Consumes POST /api/test, settings persisted through existing storage; produces sanitized per-channel test acceptance timestamp tied to saved configuration, never tokens or claimed inbox receipt.
- [x] Review Task 1 needs before defining/adding any API. Prefer current-session frontend evidence if sufficient; don't create unnecessary persistent state.
- [x] If persistence is necessary, test settings-change invalidation and failed send before adding state; test no secret exposure and concurrent access.
- [x] Run web/storage/runner tests and independent review. Record a reason if existing interfaces suffice and no code is needed.

### Task 3: Reduce installation friction
Files: scripts/build_package.py, scripts/smoke_package.py, platform launchers, tests/test_package.py/test_launcher.py, README.md/docs/user-guide.md; exact files narrowed by distribution audit before edits.
- [x] Audit shipped archive layout/launch behavior and actual supported native launcher options, signing resources and CI coverage.
- [x] Write failure tests for missing executable/internal directory, spaces/relocation and safe repeat execution.
- [x] Add the smallest usable platform launch entry points and setup diagnostics; preserve bundle contents and credentials. Verify matching checksum/user install path; no security disable.
- [x] Exercise built package with isolated HOME and native scheduling stubs; record actual versus simulated evidence.
- [x] Independent distribution QA; keep unavailable signing/notarization explicit and unfinished.

### Task 3b: Local permanent installation using the bundled runtime
Files: new wuphf/install.py, tests/test_install.py, wuphf_launcher.py/tests/test_entrypoint.py. Design: outputs/WUPHF-installation-improvement-design.md (orchestrator-selected package-first local action).
Consumes a verified, extracted frozen bundle; produces a complete permanent user-owned copy and a qualified reopen path. No network, provider, credential or scheduler changes.
- [x] Write failing tests for full/incomplete bundles, safe internal and escaping links, special files, source/destination overlap, spaces/Unicode, identical rerun, different existing target and interrupted staging.
- [x] Implement install_bundle(source: Path, destination: Path) -> Path and default_destination() -> Path; expose exact --install dispatcher for frozen bundles only. Defaults: Mac ~/Library/Application Support/WUPHF; Windows %LOCALAPPDATA%/WUPHF; Linux ~/.local/opt/WUPHF.
- [x] Stage alongside destination then promote only into absent target; identical existing target is a no-op, different existing target refuses with upgrade guidance. Preserve all existing app/data/jobs on failure and reject ambiguous paths/links.
- [x] Return installed path and existing platform launch entry, explicitly not configured/connected. Source installs follow the existing explicit fallback instead.
- [x] Run supported-Python installer/entrypoint tests and independent review; integrate package smoke, documentation and exact-commit builds before release.

### Task 4: Reliability and calendar lifecycle audit
Files: wuphf/runner.py, wuphf/google.py/google_auth.py, tests/test_runner.py/test_google.py plus related modules only for evidenced defects.
- [x] Fresh reviewer maps missing expiry/identity, account switch, failures, retry, duplicate delivery and calendar ownership paths.
- [x] Reproduce each real defect with a failing behavioral test before minimal fixes.
- [x] Test recovery/restart and unrelated-calendar preservation. Do not implement destructive cleanup without reliable ownership/account evidence.
- [x] Independent code review and full test suite pass.

### Task 5: Whole-product QA and fresh usability review
- [x] Run Python suite, Node behavior, package smoke checks and all supported-platform CI checks on integrated branch.
- [x] Inspect actual browser flow with isolated sample data: zero, available, incomplete, provider disconnected/error, unsaved/saved/test states; keyboard and reduced-motion checks; language coverage. (Reduced-motion CSS inspected; actual preference and final disconnect-retry browser action remain unverified, with tool limits recorded.)
- [x] Fresh context-free agent reviews purpose/ease/docs/current alternatives and scores independently; resolve actionable failures and repeat review without prescribing scores. (Final simulated-browser score 8.5/10; 10/10 and first-time-user evidence remain pending.)
- [ ] Record first-time-user evidence when available; maintain explicit pending gates rather than inventing 10/10.

### Task 6: Merge, version and publish
Files: VERSION, CHANGELOG.md, docs/release-readiness.md, release workflows only as required.
- [x] Bump next prerelease after integration, update screenshots/guide and precise evidence.
- [ ] Commit reviewed changes, open PR, verify checks, merge under user's existing authorization.
- [ ] Build candidate from immutable commit, inspect archives/checksums/notices, publish next beta with all options and documentation.
- [ ] Verify public downloads and final independent assessment; audit every spec requirement before marking goal complete.
