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
pyinstaller --clean --onefile --name install --manifest assets/install.manifest --version-file assets/install-version-info.txt --icon assets/install.ico install.py
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
