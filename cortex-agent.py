import ctypes
import hashlib
import os
import sys
import time
import datetime
import configparser
import threading
import subprocess
import argparse

import requests
import machineid

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent
from watchdog.observers import Observer


class FailedAgentCheckIn(Exception): pass


class FailedToUploadFile(Exception): pass


class NeedPermissions(Exception): pass


class Parser(argparse.ArgumentParser):

    def __init__(self):
        super(Parser, self).__init__()

    @staticmethod
    def optparse():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--install-task", dest="installTask", action="store_true",
            help="Install the schtasks at logon, this way the program runs at startup"
        )
        parser.add_argument(
            "--uninstall-task", dest="uninstallTask", action="store_true",
            help="Uninstall the schtask at login, useless for when the program is deleted"
        )
        return parser.parse_args()


class InstallCortexAgent(object):

    def __init__(self):
        self.task_name = "Traceix Cortex Agent"

    def install_schtask(self):
        exe_path = os.path.abspath(sys.executable)
        workdir = os.path.dirname(exe_path)

        tr = f'cmd.exe /c "cd /d {workdir} && \\"{exe_path}\\""'
        username = os.environ.get("USERNAME", "")
        cmd = [
            "schtasks", "/Create", "/F",
            "/TN", self.task_name,
            "/SC", "ONLOGON",
            "/RL", "HIGHEST",
            "/RU", username,
            "/IT",
            "/TR", tr
        ]
        subprocess.run(cmd, check=True)

    def uninstall_schtask(self):
        subprocess.run(["schtasks", "/Delete", "/TN", self.task_name, "/F"], check=False)


class AgentHandler(FileSystemEventHandler):

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        file_path = event.src_path
        print(f"File created in watch folder: {file_path}, handling file upload")
        t = threading.Thread(target=handle_file_uploads, args=(file_path,))
        t.start()


BASE_URL = "https://ai.perkinsfund.org"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def calc_shasum(path):
    h = hashlib.sha256()
    buffer = 65532
    with open(path, 'rb') as fh:
        while True:
            data = fh.read(buffer)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def get_client_id():
    if not os.path.exists('.clientid'):
        client_id = machineid.hashed_id("cortex-agent")[0:15]
        with open('.clientid', 'w') as fh:
            fh.write(str(client_id))
    else:
        client_id = open('.clientid').read().strip()
    return client_id


def handle_file_uploads(file_path):
    api_key, agent_uuid = parse_config()
    headers = {
        "x-api-key": api_key,
        "x-agent-id": agent_uuid
    }
    max_file_size = parse_config(get_accepted_size=True)
    if os.path.getsize(file_path) > int(max_file_size):
        return None
    file_data = {"file": open(file_path, 'rb')}
    url = f"{BASE_URL}/api/traceix/agent/run"
    try:
        req = requests.post(url, files=file_data, headers=headers)
    except:
        req = None
    if req is not None:
        data = req.json()
        results = None
        if data['success']:
            status = data['results']["status"]
            uuid_ = data['results']['uuid']
            is_done = False
            while not is_done:
                status_check = handle_status_check(uuid_)
                if status is None:
                    raise FailedToUploadFile(f"Failed to upload file: {file_path}")
                if "status" in status_check['results'].keys():
                    time.sleep(1)
                else:
                    results = status_check['results']
                    is_done = True
            handle_alert_upload(
                **results,
                sha256sum=calc_shasum(file_path),
                file_path=file_path
            )
        else:
            raise FailedAgentCheckIn(f"Failed to upload: {file_path}")


def handle_alert_upload(**kwargs):
    client_id = get_client_id()
    api_key, agent_uuid = parse_config()
    classification = kwargs.get("classification", "unknown")
    capa = kwargs.get("capa", None)
    exif = kwargs.get("exif", None)
    yara_rule = kwargs.get("yara", None)
    file_path = kwargs.get("file_path", "N/A")
    sha256sum = kwargs.get("sha256sum", "unknown")

    headers = {"x-api-key": api_key}
    post_data = {
        "client_id": client_id,
        "agent_uuid": agent_uuid,
        "classification": classification,
        "exif": exif,
        "yara": yara_rule,
        "capa": capa,
        "sha256_hash": sha256sum,
        "file_path": file_path
    }
    url = f"{BASE_URL}/api/traceix/agent/alert"
    try:
        req = requests.post(url, json=post_data, headers=headers)
    except:
        req = None
    if req is not None:
        data = req.json()
        if data['results']['ok']:
            print(f"File ({file_path}) uploaded successfully to alert dashboard")


def handle_status_check(uuid):
    api_key, agent_uuid = parse_config()
    headers = {"x-api-key": api_key}
    data = {"uuid": uuid, "agent_uuid": agent_uuid}
    url = f"{BASE_URL}/api/traceix/agent/status"
    try:
        req = requests.post(url, json=data, headers=headers)
    except:
        req = None
    if req is not None:
        return req.json()
    else:
        return None


def handle_check_in():
    api_key, agent_uuid = parse_config()
    headers = {"x-api-key": api_key}
    data = {"agent_uuid": agent_uuid}
    url = f"{BASE_URL}/api/traceix/agent/checkin"
    try:
        req = requests.post(url, headers=headers, json=data)
    except:
        req = None
    if req is not None:
        data = req.json()
        if data['results']['ok']:
            timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            with open('.last_check_in', 'w') as fh:
                fh.write(str(timestamp))
    else:
        raise FailedAgentCheckIn("Agent failed to check in")


def parse_config(path="agent.conf", get_alert_on=False, get_accepted_size=False, get_folder=False):
    config = configparser.ConfigParser()
    config.read(path)
    if get_folder:
        return config.get("agent_conf", "watch_folder")
    if get_alert_on:
        return config.get("agent_conf", "alert_on")
    if get_accepted_size:
        return config.get("agent_conf", "max_file_size")
    agent_uuid = config.get('agent_conf', 'uuid')
    api_key = config.get('agent_conf', 'api_key')
    return api_key, agent_uuid


def main():
    handler = AgentHandler()
    observer = Observer()
    folder = parse_config(get_folder=True)
    observer.schedule(handler, path=folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except FailedAgentCheckIn:
        print("Failed to perform agent check in")
    except FailedToUploadFile:
        print("Failed to upload a created file")
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    if not is_admin():
        raise NeedPermissions("You need elevated permissions to run this application")
    else:
        opts = Parser().optparse()
        if opts.installTask:
            InstallCortexAgent().install_schtask()
        elif opts.uninstallTask:
            InstallCortexAgent().uninstall_schtask()
        else:
            schedule = BackgroundScheduler(timezone="UTC")
            schedule.add_job(handle_check_in, IntervalTrigger(minutes=30))
            schedule.start()
            main()
