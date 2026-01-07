import os
import ctypes
import random
import subprocess

import shutil


class TaskAlreadyExists(Exception): pass


class UnableToQueryTasks(Exception): pass


class UnableToCreateTask(Exception): pass


class UnableToMoveFiles(Exception): pass


class NeedPerms(Exception): pass


INSTALL_DIR = "C:\\Program Files\\CortexAgents"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def create_install_folder():
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
    agent_name = create_name(just_agent=True)
    install_dir = f"{INSTALL_DIR}{os.path.sep}{agent_name}"
    if not os.path.exists(install_dir):
        os.makedirs(f"{INSTALL_DIR}{os.path.sep}{agent_name}")
    return install_dir


def create_name(just_agent=False, filename=None):
    if filename is None:
        filename = "agent.conf"
    try:
        with open(filename) as fh:
            for line in fh.read().split("\n"):
                if "uuid" in line:
                    if not just_agent:
                        return f"Traceix Cortex Agent - {line.split(' = ')[1].strip()}"
                    else:
                        return line.split(' = ')[1].strip()
    except:
        if just_agent:
            return None
        else:
            return f"Traceix Cortex Agent - {random.SystemRandom().randint(111111, 999999)}"


def create_schtask(installation_dir):
    task_name = create_name(filename=f"{installation_dir}{os.path.sep}agent.conf")
    proc = subprocess.Popen([
        "schtasks",
        "/Query"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if err == b'':
        out = out.decode('utf-8')
        for line in out.split("\n"):
            if task_name in line:
                raise TaskAlreadyExists(f"A task with name: {task_name} already exists")
    else:
        raise UnableToQueryTasks(err.decode("utf-8"))
    task_command = f'cmd.exe /c "cd /d ""{installation_dir}"" && ""{installation_dir}{os.path.sep}cortex-agent.exe"""'
    proc = subprocess.Popen([
        "schtasks",
        "/Create",
        "/TN", task_name,
        "/SC", "ONSTART",
        "/RU", "SYSTEM",
        "/RL", "HIGHEST",
        "/TR", task_command
    ])
    out, err = proc.communicate()
    if err:
        raise UnableToCreateTask(err.decode('utf-8'))


def move_files():
    try:
        agent_file = "cortex-agent.exe"
        agent_config = "agent.conf"
        folder_name = create_install_folder()
        shutil.move(agent_file, folder_name)
        shutil.move(agent_config, folder_name)
        return folder_name
    except Exception as e:
        raise UnableToMoveFiles(str(e))


def main():
    if not is_admin():
        raise NeedPerms("You need to run this script as an admin")
    print("Moving files to new location")
    install_dir = move_files()
    print("Files moved to new location")
    print("Creating scheduled task")
    create_schtask(install_dir)
    print("Scheduled task created successfully")
    print("Installation finished")


if __name__ == "__main__":
    main()