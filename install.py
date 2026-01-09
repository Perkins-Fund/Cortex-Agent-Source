import os
import ctypes
import random
import subprocess

import shutil
from win10toast import ToastNotifier


# class to throw exception if the task already exists
class TaskAlreadyExists(Exception): pass


# class to throw exception if we can't query the scheduled tasks
class UnableToQueryTasks(Exception): pass


# class to throw exception if we can't create the task
class UnableToCreateTask(Exception): pass


# class to throw exception if we can't move the files
class UnableToMoveFiles(Exception): pass


# class to throw exception if we don't have enough perms to run
class NeedPerms(Exception): pass


# the directory we want to install the agents into
INSTALL_DIR = "C:\\Program Files\\CortexAgents"


def is_admin():
    """
    check if the user is admin
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def perform_alert():
    """
    perform a Windows alert box
    """
    toast = ToastNotifier()
    toast.show_toast(
        title="Cortex-Agent-Installer",
        msg=f"Your Cortex Agent has been installed, for the changes to take effect please restart your PC.",
        duration=5,
        threaded=False
    )


def create_install_folder():
    """
    create the installation folder and the agent install folder
    """
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
    agent_name = create_name(just_agent=True)
    install_dir = f"{INSTALL_DIR}{os.path.sep}{agent_name}"
    if not os.path.exists(install_dir):
        os.makedirs(f"{INSTALL_DIR}{os.path.sep}{agent_name}")
    return install_dir


def create_name(just_agent=False, filename=None):
    """
    create the name for the agent scheduled task
    """
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
    """
    create the scheduled task
    """
    task_name = create_name(filename=f"{installation_dir}{os.path.sep}agent.conf")
    # query tasks first to verify we aren't making the same task twice
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
    # create the task
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
    """
    move the files to the installation location
    """
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
    """
    main function
    """
    if not is_admin():
        raise NeedPerms("You need to run this script as an admin")
    print("Moving files to new location")
    install_dir = move_files()
    print("Files moved to new location")
    print("Creating scheduled task")
    create_schtask(install_dir)
    print("Scheduled task created successfully")
    print("Installation finished")
    perform_alert()


if __name__ == "__main__":
    main()
