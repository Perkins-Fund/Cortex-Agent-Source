import ctypes
import re
import shutil
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path

BASE_DIR = Path(r"C:\Program Files\CortexAgents")
CONF_NAME = "agent.conf"
AGENT_EXE_NAME = "cortex-agent.exe"
TASK_FOLDER = r"CortexAgents"

UUID_RE = re.compile(r"^agnt-[A-Za-z0-9-]{8,}$")


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_self() -> None:
    exe = str(Path(sys.executable).resolve())
    args = " ".join(f'"{a}"' for a in sys.argv[1:])
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, args, None, 1)
    if rc <= 32:
        raise RuntimeError("Elevation was cancelled or failed.")
    sys.exit(0)


def bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    try:
        ctypes.windll.user32.MessageBoxW(None, msg, "Cortex Agent Installer", 0x10)  # MB_ICONERROR
    except Exception:
        pass
    sys.exit(code)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def run_cmd(cmd: list[str]) -> None:
    info("Running: " + " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        stderr = (p.stderr or "").strip()
        stdout = (p.stdout or "").strip()
        details = "\n".join(x for x in [stdout, stderr] if x)
        raise RuntimeError(details or f"Command failed: {' '.join(cmd)}")


def task_exists(task_name: str) -> bool:
    p = subprocess.run(["schtasks", "/Query", "/TN", task_name], capture_output=True, text=True)
    return p.returncode == 0


def main() -> None:
    if not is_admin():
        info("Not elevated; requesting admin via UAC...")
        try:
            elevate_self()
        except Exception as e:
            die(str(e))

    bdir = bundle_dir()
    conf_src = bdir / CONF_NAME
    agent_src = bdir / AGENT_EXE_NAME

    if not conf_src.exists():
        die(f"Missing {CONF_NAME} next to installer: {conf_src}")
    if not agent_src.exists():
        die(f"Missing {AGENT_EXE_NAME} next to installer: {agent_src}")

    cfg = ConfigParser()
    cfg.read(conf_src, encoding="utf-8")

    if "agent_conf" not in cfg:
        die("agent.conf missing [agent_conf] section")

    uuid = cfg.get("agent_conf", "uuid", fallback="").strip()
    if not uuid:
        die("agent.conf missing agent_conf.uuid")
    if not UUID_RE.match(uuid):
        die(f"Invalid uuid format: {uuid}")

    agent_dir = BASE_DIR / uuid

    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        die(f"Failed to create base directory {BASE_DIR}: {e}")

    if agent_dir.exists():
        die(f"Install folder already exists, refusing to continue:\n{agent_dir}")

    task_name = f"Cortex Agent {uuid}"
    if task_exists(task_name):
        die(f"Scheduled task already exists, refusing to continue:\n{task_name}")

    try:
        agent_dir.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        die(f"Install folder already exists, refusing to continue:\n{agent_dir}")
    except Exception as e:
        die(f"Failed to create install folder {agent_dir}: {e}")

    try:
        shutil.copy2(conf_src, agent_dir / CONF_NAME)
        shutil.copy2(agent_src, agent_dir / AGENT_EXE_NAME)
    except Exception as e:
        # rollback folder if copy fails
        try:
            shutil.rmtree(agent_dir, ignore_errors=True)
        except Exception:
            pass
        die(f"Failed to copy files into {agent_dir}: {e}")

    tr = f'cmd.exe /c "cd /d ""{agent_dir}"" && ""{agent_dir / AGENT_EXE_NAME}"""'

    try:
        run_cmd([
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/SC", "ONSTART",
            "/RU", "SYSTEM",
            "/RL", "HIGHEST",
            "/TR", tr,
        ])
    except Exception as e:
        # rollback on task creation failure
        try:
            # best-effort delete folder
            shutil.rmtree(agent_dir, ignore_errors=True)
        except Exception:
            pass
        die(f"Failed to create scheduled task:\n{e}")

    try:
        run_cmd(["schtasks", "/Run", "/TN", task_name])
    except Exception as e:
        info(f"Installed, but failed to start task immediately: {e}")

    msg = (
        "Installed Cortex Agent successfully.\n\n"
        f"Folder:\n{agent_dir}\n\n"
        f"Scheduled Task:\n{task_name}\n\n"
        "It will run automatically at system startup."
    )
    info(msg)
    try:
        ctypes.windll.user32.MessageBoxW(None, msg, "Cortex Agent Installer", 0x40)
    except Exception:
        pass


if __name__ == "__main__":
    main()
