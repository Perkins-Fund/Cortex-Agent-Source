import os
import shutil
import getpass
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
        "--hidden-import=win10toast",
        "--copy-metadata", "win10toast",
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=win32gui",
        "--name", "cortex-agent",
        "--manifest", "assets/cortex-agent.manifest",
        "--version-file", "assets/cortex-agent-version-info.txt",
        "--icon", "assets/cortex-agent.ico",
        "cortex-agent.py"
    ])


def sign_files():
    password = getpass.getpass("Enter signing cert password: ")
    files = ["dist\\cortex-agent.exe", "dist\\install.exe"]
    for file_ in files:
        subprocess.run([
            "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.22621.0\\x64\\signtool.exe", "sign",
            "/fd", "SHA256",
            "/f", ".\\assets\\signing_certs\\cert.pfx",
            "/P", password,
            file_
        ])


def main():
    clean_dir()
    build_installer()
    build_agent()
    sign_files()


if __name__ == "__main__":
    main()
