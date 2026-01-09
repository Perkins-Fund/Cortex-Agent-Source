import os
import shutil
import subprocess


RELEASE_DIR = "dist"
AGENT_FILENAME = f"{RELEASE_DIR}/cortex-agent.exe"
INSTALL_FILENAME = f"{RELEASE_DIR}/install.exe"


def clean_dir():
    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    os.makedirs(RELEASE_DIR)


def build_installer():
    subprocess.run([
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name", "install",
        "--uac-admin",
        "--version-file", "assets/install-version-info.txt",
        "--icon", "assets/install.ico",
        "install.py"
    ])


def build_agent():
    subprocess.run([
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name", "cortex-agent",
        "--manifest", "assets/cortex-agent.manifest",
        "--version-file", "assets/cortex-agent-version-info.txt",
        "--icon", "assets/cortex-agent.ico",
        "cortex-agent.py"
    ])


def main():
    clean_dir()
    build_installer()
    build_agent()


if __name__ == "__main__":
    main()
