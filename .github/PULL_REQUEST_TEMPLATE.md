# Cortex Agent — Pull Request

## Summary
<!-- What does this PR change? Keep it short and clear. -->

## Why
<!-- Why is this change needed? Link issues if applicable. -->
Closes #

## Scope of Changes
- [ ] Agent (watch folder / upload / logic)
- [ ] Windows notification behavior
- [ ] Installer (install.exe)
- [ ] Scheduled task / startup behavior
- [ ] Build / packaging (PyInstaller)
- [ ] Docs

## How to Test
<!-- Provide exact steps to reproduce/verify. -->

### Windows
- [ ] Build agent:
  - `pyinstaller --clean --onefile --name cortex-agent --manifest assets/cortex-agent.manifest --version-file assets/cortex-agent-version-info.txt --icon assets/cortex-agent.ico cortex-agent.py`
- [ ] Build installer:
  - `pyinstaller --clean --onefile --name install --uac-admin --version-file assets/install-version-info.txt --icon assets/install.ico install.py`
- [ ] Install with Admin: run `install.exe`
- [ ] Confirm scheduled task exists and runs
- [ ] Drop a test file into the watch folder and confirm:
  - [ ] Alert appears in Traceix dashboard
  - [ ] If classified malicious: Windows notification appears

### Linux / macOS (if applicable)
- [ ] Basic run works
- [ ] Watch folder triggers submission
- [ ] No regressions in config parsing

## Screenshots / Logs
<!-- If UI/notifications changed, include screenshots. If behavior changed, include logs. -->

## Security & Privacy Checklist
- [ ] No secrets/keys added to repo
- [ ] No sensitive file contents logged by default
- [ ] Network destinations are expected (Traceix endpoints only)
- [ ] Changes do not weaken signature / integrity checks (if applicable)

## Backward Compatibility
- [ ] Existing agent configs still work
- [ ] Existing deployments / installs still work
- [ ] Upgrade path is safe (no breaking scheduled task/paths)

## Notes for Reviewers
<!-- Anything reviewers should focus on? -->
