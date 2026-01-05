# Cortex Agent Source

Cortex Agents are a form of malware analysis agents by [Traceix](https://traceix.com?utm_source=agent-repo)

These agents watch a designated folder that the user requests. This program then sends alerts to the Traceix dashboard so that the user is able to view and mark the alerts as resolved.


# Making Cortex Agents

To make a Cortex Agent you will need to go to [Traceix](https://traceix.com?utm_source=agent-repo) and build one there

# Building From Source

```powershell
pip install -r requirements.txt
pyinstaller --onefile --name cortex-agent --manifest cortex-agent.manifest --version-file version_info.txt --icon logo.ico cortex-agent.py
```

File will be in `dist/cortex-agent*`