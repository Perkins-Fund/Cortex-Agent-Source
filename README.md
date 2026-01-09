# Cortex Agent Source

Cortex Agents are lightweight endpoint agents from [Traceix](https://traceix.com?utm_source=agent-repo) that help you monitor a folder for new files and automatically submit those files for malware analysis.

## What Cortex Agents do

When a Cortex Agent is running on your system, it:

* **Watches a folder you choose** (your “watch folder”)
* **Detects new files** added to that folder
* **Uploads files to Traceix for analysis** (based on your agent configuration)
* **Sends an alert to your Traceix dashboard**
* Lets you **review, triage, and mark alerts as resolved** in the dashboard

## Windows alerting behavior (malicious classifications)

On **Windows**, if Traceix classifies a submitted file as **malicious**, the agent will also trigger a **local Windows alert/notification** so you get an immediate heads-up on the endpoint (in addition to the dashboard alert).

---

## Support, Issue Reports, and Pull Requests (GitHub)

If something’s broken, confusing, or you have an idea — **use GitHub** so it’s tracked and visible.

### Quick links
- **Report a bug / problem:** https://github.com/Perkins-Fund/Cortex-Agent-Source/issues
- **Request a feature:** https://github.com/Perkins-Fund/Cortex-Agent-Source/issues
- **Open a pull request:** https://github.com/Perkins-Fund/Cortex-Agent-Source/pulls

> **Tip:** If issue templates are available, click **New issue** and pick the closest template (Bug / Feature / Build).

### What to include in an Issue (so we can actually reproduce it)
Please include:
- **OS + version** (Windows 10/11, Server, etc.)
- **How you installed** (Traceix deployment zip vs built from source)
- **Agent/installer version** (or commit SHA if building)
- **Steps to reproduce** (exact steps, watch folder path, what you dropped in, what happened)
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
  - your previous version → new version
  - OS/version
  - install method (Traceix zip vs built from source)
  - logs/output (redacted)

### Release notes
Each release includes notes describing:
- what changed
- any known issues
- anything you need to do after upgrading (if applicable)

---

# Creating a Cortex Agent

Cortex Agents are created and configured in Traceix.

1. Go to [Traceix](https://traceix.com?utm_source=agent-repo)
2. Create a new Cortex Agent
3. Download the deployment zip (agent + config + installer)

---

# Building From Source

You can build the agent and installer locally using Python + PyInstaller.

## Build the agent executable

```powershell
cd folder_with_agent_source
pip install -r requirements.txt
pyinstaller --clean --onefile --name cortex-agent --manifest assets/cortex-agent.manifest --version-file assets/cortex-agent-version-info.txt --icon assets/cortex-agent.ico cortex-agent.py
```

## Build the installer executable

```powershell
cd folder_with_agent_source
pip install -r requirements.txt
pyinstaller --clean --onefile --name install --uac-admin --version-file assets/install-version-info.txt --icon assets/install.ico install.py
```

Your compiled output will be in:

* `dist/cortex-agent*`

---

# Installing & Using a Cortex Agent

## 1) Download and extract

From [Traceix](https://traceix.com?utm_source=agent-repo), download your agent deployment zip (this typically includes your **agent config**, the **agent binary**, and **install.exe**). Extract the zip anywhere you like.

## 2) Run the installer (Admin)

Run `install.exe` **as Administrator**. This installs the agent and sets it up to launch automatically on the next reboot.

## 3) Start behavior

After installation, the agent will monitor the configured watch folder and send alerts to your Traceix dashboard as new files appear.
If a file is classified as **malicious**, Windows users will also see a **local notification**.

## Optional: start the scheduled task manually

If you want to start the agent without rebooting, you can run the scheduled task yourself using `schtasks.exe` (if you prefer manual control).
