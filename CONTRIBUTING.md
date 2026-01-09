# Contributing to Cortex Agent Source

Thanks for contributing! Cortex Agents are endpoint software — changes should be safe, predictable, and easy to review.

## Quick links
- Issues: https://github.com/Perkins-Fund/Cortex-Agent-Source/issues
- Pull Requests: https://github.com/Perkins-Fund/Cortex-Agent-Source/pulls

## Where to start

### Use GitHub Issues for:
- Reproducible bugs
- Feature requests
- Build/packaging problems
- Installer or scheduled-task issues

### Use GitHub Discussions for:
- Questions (“How do I…?”)
- Ideas before turning them into issues
- Sharing workflows / deployment tips

### Security issues
**Do not file public issues for vulnerabilities.** See `SECURITY.md`.

---

## Ground rules
Please keep contributions aligned with these principles:

- **Security first** (no secrets, no unsafe defaults, no risky logging)
- **Predictable installs** (especially on Windows)
- **Low noise** (avoid heavy background scanning or aggressive polling)
- **Reproducible builds** (PyInstaller builds should be deterministic where possible)
- **Small PRs win** (focused changes are easiest to review/merge)

---

## Development setup

### Requirements
- Python 3.x
- Windows recommended for installer/scheduled-task testing
- PyInstaller for building release binaries

Install dependencies:
```powershell
pip install -r requirements.txt
