import os
import datetime
import json
import redis
import logging
from config import settings
from encoder_ui.celery.discovery.redis_keys import *
import copy
import traceback


redis_con = redis.Redis(**settings.REDIS_ADDITIONAL)

logger = logging.getLogger('flask')
logger.propagate = True


def _get_containers(only_ffw:bool=False) -> (dict, datetime.datetime.date):
    data = redis_con.mget([CONTAINERS_DISCOVERY_DATA_KEY, CONTAINERS_DISCOVERY_LAST_UPDATE_KEY])
    if not data or len(data) < 2:
        msg = "Error while getting containers discovery data from redis, data is empty"
        logger.error(msg)
        raise Exception(msg)
    containers,  dt = data
    containers, dt = containers.decode('utf-8'), dt.decode('utf-8')
    try:
        containers = json.loads(containers)
    except TypeError as e:
        msg = 'Error while loads containers discovery data from json. Data: {}, Error: {}'.format(containers, str(e))
        raise TypeError(msg)
    try:
        dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        msg = 'Error while loads containers discovery datetime data. Data: {}, Error: {}'.format(dt, str(e))
        raise ValueError(msg)
    if only_ffw:
        deleted_containers = []
        for cnt_id, data in containers.items():
            if data and 'ff_wrapper' not in data:
                deleted_containers.append(id)
                continue
            if data and not data['ff_wrapper']:
                deleted_containers.append(id)
                continue
        for cnt_id in deleted_containers:
            del containers[cnt_id]
    containers = [x for x in containers if 'name' in x and 'id' in x]
    return containers, dt


def _get_resources() -> (dict, datetime.datetime.date):
    data = redis_con.mget([RESOURCES_DISCOVERY_DATA_KEY, RESOURCES_DISCOVERY_LAST_UPDATE_KEY])
    if not data or len(data) < 2:
        msg = "Error while getting resources discovery data from redis, data is empty"
        logger.error(msg)
        raise Exception(msg)
    resources,  dt = data
    resources, dt = resources.decode('utf-8'), dt.decode('utf-8')
    try:
        resources = json.loads(resources)
    except TypeError as e:
        msg = 'Error while loads resources discovery data from json. Data: {}, Error: {}'.format(resources, str(e))
        raise TypeError(msg)
    try:
        dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        msg = 'Error while loads resources discovery datetime data. Data: {}, Error: {}'.format(dt, str(e))
        raise ValueError(msg)
    return resources, dt


def _find_container_logs_dir(container_name:bool):
    dirs = os.listdir(settings.LOGS_PATH)
    dirs = [d for d in dirs if d == f'ff_wrapper_{container_name}']
    dirs = [d for d in dirs if os.path.isdir(os.path.join(settings.LOGS_PATH, d))]
    if len(dirs) == 1:
        return os.path.join(settings.LOGS_PATH, dirs[0])
    else:
        containers, _ = _get_containers()
        container_id = None
        for container in containers:
            if container['name'] == container_name:
                container_id = container['id']
        if container_id:
            dirs = os.listdir(settings.LOGS_PATH)
            dirs = [d for d in dirs if d == f'ff_wrapper_{container_id}']
            dirs = [d for d in dirs if os.path.isdir(os.path.join(settings.LOGS_PATH, d))]
            if len(dirs) == 1:
                return os.path.join(settings.LOGS_PATH, dirs[0])
    return None

def _sort_file_logs(logs: dict) -> dict:
    """
    Sort logs by datetime + sort by logrotation number in end of file
    logs: logs from _get_container_log_files - {'dt': datetime, 'filename': filename }
    """
    def _sort(el):
        dt = el['dt']
        if not el['filename'].endswith('.log'):
            try:
                delta = int(el['filename'].split('.')[-1])
                # First newest name endswith .log.0, but it's older, than .log
                delta += 1
            except ValueError:
                delta = 0
            dt = dt - datetime.timedelta(milliseconds=delta)
        return dt

    sorted_logs =  sorted(logs, reverse=True, key=_sort)
    return sorted_logs

def _get_container_log_files(logs_path: str):
    files = os.listdir(logs_path)
    files = [f for f in files if '.log' in f and os.path.isfile(os.path.join(logs_path, f))]
    files = sorted(files, reverse=True)
    result = {'manager': [], 'ffmpeg': []}
    for f in files:
        dt = f.replace('manager_', '').replace('ffmpeg_', '')
        dt = dt.split('.')[0]
        try:
            dt = datetime.datetime.strptime(dt, '%Y_%m_%d__%H_%M_%S')
        except ValueError:
            logger.warning(f"Wrong dt detected while listing logs in {logs_path} - {f}")
            logger.debug(traceback.format_exc())
            continue
        if f.startswith('manager_'):
            obj = {'dt': dt, 'filename': f}
            result['manager'].append(obj)
        if f.startswith('ffmpeg_'):
            obj = {'dt': dt, 'filename': f}
            result['ffmpeg'].append(obj)
    for key in result.keys():
        result[key] = _sort_file_logs(result[key])
    for value in result.values():
        for obj in value:
            obj['dt'] = obj['dt'].strftime('%Y-%m-%d %H:%M:%S')
    return result 

def _get_file_path(logs_path: str, files: dict, file_name: str):
    file_path = ''
    for files_objects in files.values():
        for f in files_objects:
            if f['filename'] == file_name:
                file_path = f['filename']
    if file_path:
        file_path = os.path.join(logs_path, file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return file_path
    return None


def _filter_ffprobe_streams(streams_info: dict) -> dict:
    streams_info = copy.deepcopy(streams_info)
    if not 'programs' in streams_info:
        return streams_info
    streams_id_from_programs = []
    streams_without_program = []
    for el in streams_info['programs']:
        if 'streams' not in el:
            continue
        streams_id_from_programs += [x['index'] for x in el['streams']]
    for stream in streams_info['streams']:
        if stream['index'] not in streams_id_from_programs:
            streams_without_program.append(stream)
    streams_info['streams'] = streams_without_program
    return streams_info


def _is_addr_valid(addr:str):
    chars = [' ', ';', '\\', r'\n', r'\t', '>', '<']
    for char in chars:
        if char in addr:
            return False
    return True
