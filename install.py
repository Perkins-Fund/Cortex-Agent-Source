import os
import sys
import time
import ctypes
import random
import subprocess
import shutil


# Exceptions
class TaskAlreadyExists(Exception): pass


class UnableToQueryTasks(Exception): pass


class UnableToCreateTask(Exception): pass


class UnableToMoveFiles(Exception): pass


class NeedPerms(Exception): pass


class FailedToStartTask(Exception): pass


class UnableToWriteRunner(Exception): pass


INSTALL_DIR = r"C:\Program Files\CortexAgents"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _parse_uuid_from_conf(conf_path: str) -> str | None:
    """
    Read agent.conf and attempt to extract uuid value.
    Accepts formats like:
      uuid = abc
      uuid=abc
      uuid : abc
    """
    try:
        with open(conf_path, "r", encoding="utf-8", errors="ignore") as fh:
            for raw in fh.read().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "uuid" not in line.lower():
                    continue

                # crude but tolerant parse
                # prefer splitting on '='
                if "=" in line:
                    left, right = line.split("=", 1)
                    if "uuid" in left.lower():
                        val = right.strip().strip('"').strip("'")
                        return val or None

                # fallback split on ':'
                if ":" in line:
                    left, right = line.split(":", 1)
                    if "uuid" in left.lower():
                        val = right.strip().strip('"').strip("'")
                        return val or None
    except Exception:
        return None

    return None


def create_name(just_agent: bool = False, filename: str = "agent.conf") -> str:
    """
    Create the name for the agent scheduled task (or agent folder name).
    """
    uuid_val = _parse_uuid_from_conf(filename)
    if uuid_val:
        return uuid_val if just_agent else f"Traceix Cortex Agent - {uuid_val}"

    # fallback if agent.conf missing or no uuid present
    if just_agent:
        return f"agnt-{random.SystemRandom().randint(111111, 999999)}"
    return f"Traceix Cortex Agent - {random.SystemRandom().randint(111111, 999999)}"


def create_install_folder() -> str:
    """
    Create base install folder and agent-specific folder.
    """
    os.makedirs(INSTALL_DIR, exist_ok=True)

    agent_folder_name = create_name(just_agent=True)
    install_dir = os.path.join(INSTALL_DIR, agent_folder_name)
    os.makedirs(install_dir, exist_ok=True)
    return install_dir


def move_files() -> str:
    """
    Move cortex-agent.exe and agent.conf into the install folder.
    """
    try:
        agent_file = "cortex-agent.exe"
        agent_config = "agent.conf"

        folder_name = create_install_folder()

        shutil.move(agent_file, os.path.join(folder_name, agent_file))
        shutil.move(agent_config, os.path.join(folder_name, agent_config))

        return folder_name
    except Exception as e:
        raise UnableToMoveFiles(str(e))


def write_runner_script(installation_dir: str) -> str:
    """
    Create a short runner script *inside* the agent folder to keep /TR short.
    Uses %~dp0 so it always runs relative to its own directory.
    """
    try:
        script_path = os.path.join(installation_dir, "run_agent.cmd")

        contents = (
            "@echo off\r\n"
            "setlocal\r\n"
            "cd /d \"%~dp0\"\r\n"
            "\"%~dp0cortex-agent.exe\" >> \"%~dp0task.log\" 2>&1\r\n"
        )

        with open(script_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(contents)

        return script_path
    except Exception as e:
        raise UnableToWriteRunner(str(e))


def create_schtask(installation_dir: str) -> str:
    """
    Create the scheduled task, pointing /TR at the runner script in the install dir.
    """
    conf_path = os.path.join(installation_dir, "agent.conf")
    task_name = create_name(filename=conf_path)

    # Query tasks first to verify we aren't making the same task twice
    q = subprocess.run(
        ["schtasks", "/Query", "/FO", "LIST"],
        capture_output=True,
        text=True,
        shell=False
    )
    if q.returncode != 0:
        raise UnableToQueryTasks(q.stderr.strip() or q.stdout.strip())

    if task_name.lower() in q.stdout.lower():
        raise TaskAlreadyExists(f"A task with name: {task_name} already exists")

    # Write runner script in install folder
    runner_path = write_runner_script(installation_dir)

    # Keep /TR short: just call the .cmd directly
    # (Quoting is still correct if there are spaces)
    task_command = f"\"{runner_path}\""

    c = subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/SC", "ONSTART",
            "/RU", "SYSTEM",
            "/RL", "HIGHEST",
            "/TR", task_command,
            "/F",  # overwrite if it exists (we already checked, but this helps if case/format differs)
        ],
        capture_output=True,
        text=True,
        shell=False
    )

    if c.returncode != 0:
        raise UnableToCreateTask((c.stderr.strip() or c.stdout.strip() or "Unknown schtasks error").strip())

    return task_name


def start_scheduled_task(task_name: str) -> None:
    r = subprocess.run(
        ["schtasks", "/Run", "/TN", task_name],
        capture_output=True,
        text=True,
        shell=False
    )
    if r.returncode != 0:
        raise FailedToStartTask(r.stderr.strip() or r.stdout.strip() or f"Failed to start task: {task_name}")


def print_step(step_name, status="wait"):
    if status == "wait":
        print(f"  ├─ {step_name} ", end="")
        sys.stdout.flush()
        for _ in range(4):
            time.sleep(0.4)
            print(".", end="", flush=True)
        print("\b\b\b   ", end="\r")
    elif status == "ok":
        print(f"\r  │  └─ {step_name}  ✓")
    elif status == "error":
        print(f"\r  │  └─ {step_name}  ✗")


def main():
    if not is_admin():
        raise NeedPerms("You need to run this script as an admin")

    print("Starting installation process...\n")

    print_step("Moving files to new location")
    install_dir = move_files()
    print_step("Moving files", "ok")

    print_step("Writing runner script (run_agent.cmd)")
    runner = write_runner_script(install_dir)
    print_step(f"Runner script created: {runner}", "ok")

    print_step("Creating scheduled task")
    task_name = create_schtask(install_dir)
    print_step("Creating scheduled task", "ok")
    print_step(f"Scheduled task created under {task_name}", "ok")

    print_step(f"Attempting to start scheduled task: {task_name}")
    time.sleep(2)
    try:
        start_scheduled_task(task_name)
        print_step("Scheduled task started successfully", "ok")
        started = True
    except Exception:
        print_step("Failed to start scheduled task", "error")
        started = False

    print("  └─ Installation finished  ✓\n")

    if not started:
        print("╔════════════════════════════════════════════════════╗")
        print("║    YOU WILL NEED TO RESTART YOUR COMPUTER NOW      ║")
        print("╚════════════════════════════════════════════════════╝\n")
    else:
        print("╔════════════════════════════════════════════════════╗")
        print("║    RESTART YOUR COMPUTER AT YOUR CONVENIENCE       ║")
        print("╚════════════════════════════════════════════════════╝\n")

    time.sleep(10)


if __name__ == "__main__":
    main()
