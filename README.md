# Cortex Agent Source (Traceix)

Cortex Agents are **triage drop zones** for suspicious files.

Instead of “monitor everything everywhere,” Cortex Agents focus on one job:
**turn “what is this file?” into a fast, consistent answer**.

You point an agent at a **dedicated folder**. When new files appear, the agent submits them to Traceix and creates **actionable alerts** in your dashboard.

> **Not an EDR:** Cortex Agents do **not** continuously monitor processes/memory, collect endpoint telemetry, or provide containment/isolation controls. They’re built for **file intake + triage**.

---

## What Cortex Agents do (the drop zone model)

When a Cortex Agent is running, it:

- **Watches a folder you choose** (your “drop zone”)
- **Detects new files** added to that folder
- **Submits those files to Traceix** (based on your agent configuration)
- **Creates an alert** in your Traceix dashboard
- Lets you **review, triage, export JSON, and mark items reviewed/resolved**

### Why this exists (and why it’s not an EDR)
EDR is a different category: always-on telemetry, deep hooks, ongoing tuning, and lots of noise.

Cortex Agents are intentionally lighter:
- **Faster to deploy** (one intake lane can serve a person or a team)
- **Easier to operate** (drop file → get answer → act)
- **Lower overhead** (results + alerts, not nonstop endpoint telemetry)

**Bottom line:** EDRs monitor everything all the time. Cortex Agents answer one question extremely well:  
**“Is this file safe?”**

---

## Who this is for

Cortex Agents are for **everyone** — not just big security teams:

- **Solo users**: a personal “file check” lane for downloads/attachments
- **Small teams / IT**: one shared intake folder that standardizes triage
- **SOC / DFIR**: consistent enrichment + repeatable evidence packaging
- **Enterprises / MSPs**: standardized triage lanes without adding another always-on platform

---

## Common use cases

- Email attachment triage
- User-reported “is this safe?” intake
- Suspicious download quarantine folder
- SOC alert enrichment and evidence packaging
- Separate intake lanes by workflow (file type, team, customer, etc.)

---

## Windows alerting behavior (malicious classifications)

On **Windows**, if Traceix classifies a submitted file as **malicious**, the agent can also trigger a **local Windows notification** so you get an immediate heads-up on the endpoint (in addition to the dashboard alert).

---

## Quick start (recommended workflow)

1. **Create an agent in Traceix**
2. **Download the deployment zip** (agent + config + installer)
3. **Install it once** on a workstation or server
4. Use the configured folder as your **intake drop zone**
5. **Drop files in** → results show up as **dashboard alerts**

> **Important:** Always point Cortex at a **dedicated folder** (e.g., `C:\Samples\` or `/home/user/samples`).  
> Avoid watching root/system folders (`C:\`, `/`, `/root`, etc.) — too many files can cause high CPU/disk usage and alert spam.

---

## Installing & using a Cortex Agent

### 1) Download and extract
From [Traceix](https://traceix.com?utm_source=agent-repo), download your agent deployment zip (typically includes your **agent config**, the **agent binary**, and **install.exe**). Extract it anywhere.

### 2) Run the installer (Admin)
Run `install.exe` **as Administrator**. This installs the agent and sets it up to launch automatically on the next reboot.

### 3) Start behavior
After installation, the agent monitors the configured drop-zone folder and creates alerts in your Traceix dashboard as new files appear.

---

## Support, Issue Reports, and Pull Requests (GitHub)

If something’s broken, confusing, or you have an idea — **use GitHub** so it’s tracked and visible.

### Quick links
- **Report a bug / problem:** https://github.com/Perkins-Fund/Cortex-Agent-Source/issues
- **Request a feature:** https://github.com/Perkins-Fund/Cortex-Agent-Source/issues
- **Open a pull request:** https://github.com/Perkins-Fund/Cortex-Agent-Source/pulls

> **Tip:** If issue templates are available, click **New issue** and pick the closest template (Bug / Feature / Build).

### What to include in an Issue (so we can reproduce it)
Please include:
- **OS + version** (Windows 10/11, Server, etc.)
- **How you installed** (Traceix deployment zip vs built from source)
- **Agent/installer version** (or commit SHA if building)
- **Steps to reproduce** (watch folder path, what you dropped in, what happened)
- **Logs / console output** (remove secrets/tokens)

### Pull request guidelines (fast approvals)
PRs are welcome — keep them easy to review:
- One focused change per PR (or clearly grouped changes)
- Include testing notes (Windows installer / scheduled task behavior if touched)
- Don’t commit secrets, tokens, or real customer configs
- If changing watch-folder behavior, mention performance impact + edge cases

### Security / vulnerability reports
**Please do not open public issues for security vulnerabilities.**  
If you believe you found a security issue, report it privately via the repository’s **Security** tab (if enabled) or through Traceix support (contact@perkinsfund.org).

---

## Releases & Versioning

### Where to get releases
Official builds are published on GitHub Releases:  
https://github.com/Perkins-Fund/Cortex-Agent-Source/releases

> If you downloaded a Cortex Agent from Traceix, you are already using an official deployment package (agent + config + installer).

### Version format
Cortex Agents use a **4-part** version format:

**`major.minor.patch.push`**  
Example: **`1.0.0.0`**

- **major** — breaking changes (behavior/config/install changes that may require attention)
- **minor** — new features or meaningful improvements (backwards-compatible when possible)
- **patch** — bug fixes and small corrections
- **push** — re-build / packaging-only updates (no code change intended), hotfix repacks, or rapid deployment iterations

### Upgrade guidance
- If you’re upgrading across a **major** version, read the release notes carefully.
- If you hit a regression after upgrading, please open an issue and include:
  - previous version → new version
  - OS/version
  - install method (Traceix zip vs built from source)
  - logs/output (redacted)

### Release notes
Each release includes notes describing:
- what changed
- any known issues
- anything you need to do after upgrading (if applicable)

---

## Creating a Cortex Agent

Cortex Agents are created and configured in Traceix.

1. Go to [Traceix](https://traceix.com?utm_source=agent-repo)
2. Create a new Cortex Agent
3. Download the deployment zip (agent + config + installer)

---

## Building from source

You can build the agent and installer locally using Python + PyInstaller.

### Build the agent executable
```powershell
cd folder_with_agent_source
pip install -r requirements.txt
pyinstaller --clean --onefile --name cortex-agent --manifest assets/cortex-agent.manifest --version-file assets/cortex-agent-version-info.txt --icon assets/cortex-agent.ico cortex-agent.py
````

### Build the installer executable

```powershell
cd folder_with_agent_source
pip install -r requirements.txt
pyinstaller --clean --onefile --name install --uac-admin --version-file assets/install-version-info.txt --icon assets/install.ico install.py
```

Compiled output will be in:

* `dist/cortex-agent*`

