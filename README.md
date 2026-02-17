# Cortex Agent Source (Traceix)

Cortex Agents are **Triage Drop Zones** for suspicious files.

They’re designed around one simple workflow:

**Drop a file into a dedicated folder, get a fast, consistent answer in Traceix.**

Instead of trying to monitor everything on the endpoint, a Cortex Agent focuses on file intake: it watches a folder you choose, submits new files to Traceix, and creates **actionable alerts** in your dashboard.

> **Not an EDR:** Cortex Agents do **not** continuously monitor processes/memory, collect endpoint telemetry, or provide containment/isolation controls. They exist for **file intake + triage**.

---

## The Triage Drop Zone model

A **Triage Drop Zone** is a dedicated folder used only for suspicious file intake.

When the agent is running, it:

* **Watches your chosen drop-zone folder**
* **Detects new files** added to that folder
* **Waits until the file is fully written** (prevents 0-byte / partial downloads)
* **Submits the file to Traceix** using your agent credentials
* **Creates an alert** in your Traceix dashboard
* Optionally shows a **local Windows toast notification** when a file is classified as **malicious**

### Why a dedicated folder matters

Pointing the agent at system folders or "busy" directories causes noise and performance issues.

Recommended:

* `C:\Samples\`
* `C:\Triage\`
* `C:\Users\<you>\Downloads\Triage\`

Avoid:

* `C:\`
* `C:\Windows\`
* Your entire `Downloads\` root (too many non-suspicious files)
* Any folder with constant background churn (build output, package caches, etc.)

---

## What gets ignored (in-progress downloads)

Browsers and downloaders often create a temporary file first, then rename it when complete. To prevent processing partial files, the agent ignores common "still downloading" suffixes:

* `.crdownload` (Chrome / Edge)
* `.part` (Firefox)
* `.partial`
* `.tmp`

Once the final file appears without these extensions, the agent queues it for analysis.

---

## Path shortcuts (watch-folder "tricks")

Cortex Agents support path shortcuts so you don’t have to type full Windows paths in config.
These shortcuts are expanded at runtime when the agent reads `watch_folder`.

### Supported shortcuts

| Shortcut         | Expands to                                                                          |
| ---------------- | ----------------------------------------------------------------------------------- |
| `!USER!`         | your Windows username                                                               |
| `!USERHOME!`     | `C:\Users\{username}`                                                               |
| `!LOCALTEMP!`    | `C:\Users\{username}\AppData\Local\Temp`                                            |
| `!ROAM!`         | `C:\Users\{username}\AppData\Roaming`                                               |
| `!PROGDATA!`     | `C:\ProgramData`                                                                    |
| `!APPDATA!`      | `C:\Users\{username}\AppData`                                                       |
| `!WINTEMP!`      | `C:\Windows\Temp`                                                                   |
| `!USERSTART!`    | `C:\Users\{username}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup` |
| `!ALLUSERSTART!` | `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup`                      |

### Examples

**Example 1 — dedicated triage folder in your home directory**

```ini
watch_folder = !USERHOME!\Samples
```

**Example 2 — triage folder inside local temp**

```ini
watch_folder = !LOCALTEMP!\CortexDrop
```

**Example 3 — shared drop zone for multiple users**

```ini
watch_folder = !PROGDATA!\Traceix\DropZone
```

> Tip: If you use `!PROGDATA!`, create the folder once and set permissions so the intended users/tools can write to it.

---

## Quick start (recommended workflow)

1. **Create an agent in Traceix**
2. **Download the deployment zip** (agent + config + installer)
3. **Install it once** on a workstation or server
4. Use the configured folder as your **Triage Drop Zone**
5. **Drop files in**, results show up as **dashboard alerts**

---

## Windows alerting behavior (malicious classifications)

On Windows, if Traceix classifies a submitted file as **malicious**, the agent can trigger a **local Windows notification** in addition to creating the dashboard alert.

---

## Support, Issue Reports, and Pull Requests (GitHub)

If something’s broken, confusing, or you have an idea — use GitHub so it’s tracked and visible.

* Report a bug / problem: [https://github.com/Perkins-Fund/Cortex-Agent-Source/issues](https://github.com/Perkins-Fund/Cortex-Agent-Source/issues)
* Request a feature: [https://github.com/Perkins-Fund/Cortex-Agent-Source/issues](https://github.com/Perkins-Fund/Cortex-Agent-Source/issues)
* Open a pull request: [https://github.com/Perkins-Fund/Cortex-Agent-Source/pulls](https://github.com/Perkins-Fund/Cortex-Agent-Source/pulls)

**For issues, include:**

* OS + version
* install method (Traceix zip vs built from source)
* agent/installer version (or commit SHA)
* steps to reproduce (watch folder path, what you dropped in, what happened)
* logs/output (redact secrets)

**Security reports:** don’t file public issues for vulnerabilities—use the repo Security tab (if enabled) or email [contact@perkinsfund.org](mailto:contact@perkinsfund.org).
