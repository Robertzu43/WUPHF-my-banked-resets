# Cross-platform WUPHF implementation plan

> **For agentic workers:** Use superpowers:executing-plans and verify each independently testable task.

Goal: support Windows, macOS and common Linux desktops without weakening secret storage or disrupting existing Mac settings.

1. Make storage locking and atomic writes portable, preserving concurrent-run protection. Test platform-specific behavior and run an actual Linux smoke test.
2. Keep existing macOS Keychain storage; on Windows and Linux use only trusted operating-system credential backends through keyring, fail clearly if unavailable, and test no plaintext fallback.
3. Add per-user Windows Task Scheduler and Linux systemd user timers while retaining launchd on macOS. Test installation, existing-job protection, failure rollback and uninstall.
4. Provide clear installation and dependency guidance for all three systems, update interface translations to say computer, and avoid claiming unsupported environments work.
5. Run the full suite and Linux smoke checks; identify any platforms not available for native end-to-end verification.
