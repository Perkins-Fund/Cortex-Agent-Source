import ctypes
import hashlib
import os
import time
import datetime
import configparser
from concurrent.futures import ThreadPoolExecutor
import logging
from logging.handlers import RotatingFileHandler

import requests
import machineid
import psutil
from win10toast import ToastNotifier

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent
from watchdog.observers import Observer


# class to hold check in failures exception
class FailedAgentCheckIn(Exception): pass


# class to hold upload failures exception
class FailedToUploadFile(Exception): pass


# class to hold permission failures exception
class NeedPermissions(Exception): pass


# class to hold config missing exception
class NoConfigFound(Exception): pass


# log file name
LOG_FILE = "cortex-agent.log"


def setup_logging():
    """
    setup the logging mechanism so that we log to output and to file and rotate the log files
    """
    logger = logging.getLogger("cortex-agent")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)sZ [%(levelname)s] %(threadName)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    # rotate logs every 5MB, max of 3 log files
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger


class AgentHandler(FileSystemEventHandler):
    """
    handler for file system events
    """
    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        # skip directories
        if getattr(event, "is_directory", False):
            return

        file_path = event.src_path
        LOG.info(f"File created in watch folder: {file_path}, queued for analysis")

        try:
            # add the file to the executor and upload it
            EXECUTOR.submit(handle_file_uploads, file_path)
        except RuntimeError:
            return


# logger
LOG = setup_logging()

# max concurrent processes so we don't overload the computer
# max is: (CPU_COUNT / 2) - 1 || 1
# minimum number is 1
MAX_CONCURRENT_ANALYSES = round((psutil.cpu_count(logical=False) / 2) - 1)
if MAX_CONCURRENT_ANALYSES == 0:
    MAX_CONCURRENT_ANALYSES = 1
# the variable that holds the processes
EXECUTOR = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_ANALYSES)
# base URL for the API
BASE_URL = "http://172.25.108.61:5132"


def is_admin():
    """
    check if the user is an admin
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def perform_alert(file_path):
    """
    perform a Windows alert box
    """
    toast = ToastNotifier()
    toast.show_toast(
        title="Cortex-Agent Alert",
        msg=f"File: {file_path} has been identified as malicious, an alert has been uploaded to the Traceix dashboard",
        duration=4,
        threaded=True
    )


def calc_shasum(path):
    """
    calculate the SHA-256 sum of a file
    """
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
    """
    get or generate a client_id for the users system
    """
    if not os.path.exists('.clientid'):
        client_id = machineid.hashed_id("cortex-agent")[0:15]
        with open('.clientid', 'w') as fh:
            fh.write(str(client_id))
    else:
        client_id = open('.clientid').read().strip()
    return client_id


def handle_file_uploads(file_path):
    """
    handle the file uploads
    """
    try:
        if not os.path.isfile(file_path):
            return None
    except Exception:
        return None

    api_key, agent_uuid = parse_config()
    headers = {
        "x-api-key": api_key,
        "x-agent-id": agent_uuid
    }

    max_file_size = parse_config(get_accepted_size=True)
    try:
        if os.path.getsize(file_path) > int(max_file_size):
            LOG.info(f"Skipping (too large): {file_path}")
            return None
    except Exception:
        return None

    url = f"{BASE_URL}/api/traceix/agent/run"
    LOG.info(f"Submitting for analysis: {file_path}")

    try:
        with open(file_path, 'rb') as f:
            file_data = {"file": f}
            req = requests.post(url, files=file_data, headers=headers)
    except Exception:
        LOG.exception(f"Upload failed (request error): {file_path}")
        req = None

    if req is not None:
        try:
            data = req.json()
        except Exception:
            LOG.exception(f"Upload failed (invalid JSON response): {file_path}")
            return None
        results = None
        if data.get('success'):
            LOG.info(f"File: {file_path} submitted successfully, starting waiting process")
            uuid_ = data.get("results", {}).get("uuid")
            if not uuid_:
                LOG.error(f"Upload succeeded but missing uuid in response: {file_path}")
                return None

            is_done = False
            did_fail = False
            wait_time = 360
            waited = 0
            while not is_done:
                LOG.debug("Waiting for analysis to complete")
                status_check = handle_status_check(uuid_)
                if status_check is None:
                    raise FailedToUploadFile(f"Failed to upload file: {file_path}")

                if "status" in status_check.get('results', {}).keys():
                    # break if we hit a certain time limit so we don't overload the log file
                    if waited >= wait_time:
                        did_fail = True
                        is_done = True
                        break
                    time.sleep(5)
                    waited += 5
                else:
                    results = status_check['results']
                    is_done = True
            if not did_fail:
                handle_alert_upload(
                    **results,
                    sha256sum=calc_shasum(file_path),
                    file_path=file_path
                )
            else:
                LOG.error(f"Failed to upload file: {file_path} waited for 120 seconds, skipping")
        else:
            raise FailedAgentCheckIn(f"Failed to upload: {file_path}")


def handle_alert_upload(**kwargs):
    """
    upload the alert to the Traceix dashboard
    """
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
    except Exception:
        LOG.exception(f"Alert upload failed (request error): {file_path}")
        req = None

    if classification.lower() == "malicious":
        LOG.warning(f"File: {file_path} identified as malicious")
        perform_alert(file_path)

    if req is not None:
        try:
            data = req.json()
        except Exception:
            LOG.exception(f"Alert upload failed (invalid JSON response): {file_path}")
            return None

        if data.get('results', {}).get('ok'):
            LOG.info(f"Alert uploaded successfully: {file_path} sha256={sha256sum}")
        else:
            LOG.error(f"Alert upload failed (server said not ok): {file_path}")


def handle_status_check(uuid):
    """
    handle the status checking of the file upload
    """
    api_key, agent_uuid = parse_config()
    headers = {"x-api-key": api_key}
    data = {"uuid": uuid, "agent_uuid": agent_uuid}
    url = f"{BASE_URL}/api/traceix/agent/status"
    try:
        req = requests.post(url, json=data, headers=headers)
    except Exception:
        LOG.exception(f"Status check failed (request error): uuid={uuid}")
        req = None
    if req is not None:
        try:
            return req.json()
        except Exception:
            LOG.exception(f"Status check failed (invalid JSON response): uuid={uuid}")
            return None
    else:
        return None


def handle_check_in():
    """
    handle the agent check-ins
    :return:
    """
    LOG.info("Performing agent check in")
    api_key, agent_uuid = parse_config()
    headers = {"x-api-key": api_key}
    data = {"agent_uuid": agent_uuid}
    url = f"{BASE_URL}/api/traceix/agent/checkin"
    try:
        req = requests.post(url, headers=headers, json=data)
    except Exception:
        LOG.exception("Agent check-in failed (request error)")
        req = None

    if req is not None:
        try:
            data = req.json()
        except Exception:
            LOG.exception("Agent check-in failed (invalid JSON response)")
            return None

        if data.get('results', {}).get('ok'):
            timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            with open('.last_check_in', 'w') as fh:
                fh.write(str(timestamp))
            LOG.info("Agent check-in ok")
        else:
            raise FailedAgentCheckIn("Agent failed to check in (server returned not ok)")
    else:
        raise FailedAgentCheckIn("Agent failed to check in")


def parse_config(path="agent.conf", get_alert_on=False, get_accepted_size=False, get_folder=False):
    """
    parse the configuration file
    """
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
    """
    main function
    """
    handler = AgentHandler()
    observer = Observer()
    folder = parse_config(get_folder=True)

    LOG.info(f"Starting watcher on folder: {folder}")
    LOG.info(f"Max concurrent analyses: {MAX_CONCURRENT_ANALYSES}")
    LOG.info(f"Logging to: {LOG_FILE} (rotating)")

    observer.schedule(handler, path=folder, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except FailedAgentCheckIn:
        LOG.exception("Failed to perform agent check in")
    except FailedToUploadFile:
        LOG.exception("Failed to upload a created file")
    finally:
        observer.stop()
        observer.join()
        EXECUTOR.shutdown(wait=True)
        LOG.info("Shutdown complete")


if __name__ == '__main__':
    if not os.path.exists("agent.conf"):
        raise NoConfigFound("There is not a valid config file available")
    if not is_admin():
        raise NeedPermissions("You need elevated permissions to run this application")
    else:
        handle_check_in()
        schedule = BackgroundScheduler(timezone="UTC")
        schedule.add_job(handle_check_in, IntervalTrigger(minutes=30))
        schedule.start()
        main()
