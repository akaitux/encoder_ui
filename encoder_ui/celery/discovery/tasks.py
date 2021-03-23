from celery.schedules import crontab
from encoder_ui.celery.tasks import celery
import docker
import os
import logging
import time
import csv
import redis 
from config import settings
import requests
import traceback
import datetime
import pytz
from pytz import timezone
import json
from .redis_keys import *


DEFAULT_WORKDIR = '/tmp/ff_wrapper'
LAST_DOCKER_LOGS_COUNT = 300
DISCOVERY_PERIOD = 1
DOCKER_SOCK = 'unix://var/run/docker.sock'
NVIDIA_STATS_DIR = '/var/run/nvidia_stats/'


redis_con = redis.Redis(**settings.REDIS_ADDITIONAL)
logger = logging.getLogger('celery')
logger.propagate = True


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
        sender.add_periodic_task(DISCOVERY_PERIOD, containers_discovery.s(), name='containers_discovery', expires=20)
        sender.add_periodic_task(DISCOVERY_PERIOD, resources_discovery.s(), name='resources_discovery', expires=20)

def _lock(lock_key: str) -> bool:
    """
        returned True if lock is success, False if already locked
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lock_status = redis_con.setnx(lock_key, now)
    # True - lock is setted, False - already locked
    if not lock_status:
        last_update = redis_con.get(lock_key)
        if last_update:
            last_update = last_update.decode('utf-8')
            try:
                last_update = datetime.datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logger.warning("Some error while getting redis {} key data - invalid data format".format(lock_key))
                redis_con.delete(lock_key)
                return False 
            # Проверка на залипание, если последний раз обновление было недавно, то всё ок и нужно завершать текущую задачу.
            if datetime.datetime.now() - last_update < datetime.timedelta(seconds=DISCOVERY_PERIOD * 10):
                return False
        redis_con.delete(CONTAINERS_DISCOVERY_LOCK_KEY)
    return True


def _parse_docker_dt(dt: str) -> datetime.datetime.date:
    """
    :returned - dt object
    """
    if not dt:
        return
    dt = dt.split('.')[0]
    dt = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
    return dt


@celery.task
def resources_discovery():
    if not _lock(RESOURCES_DISCOVERY_LOCK_KEY):
        logger.warning('resources discovery locked by another celery thread')
        return
    nvidia_stats = _collect_nvidia_stats()
    sysstat = _collect_system_stats()
    sysstat['gpu'] = nvidia_stats
    try:
        json_data = json.dumps(sysstat)
        redis_con.set(RESOURCES_DISCOVERY_DATA_KEY, json_data)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        redis_con.set(RESOURCES_DISCOVERY_LAST_UPDATE_KEY, now)
        logger.info('Resources discovery updated at {}'.format(now))
    except TypeError as e:
        logger.error("Error while trying write containers_discovery data to redis: {}".format(str(e)))
    redis_con.delete(RESOURCES_DISCOVERY_LOCK_KEY)


def _collect_system_stats() -> dict:
    load_avg = os.getloadavg()
    result = {
        'cpu_load_avg': load_avg,
        'cores': len(os.sched_getaffinity(0)),
        'mem': _get_meminfo()
    }
    return result

def _get_meminfo() -> dict:
    """
    Returned dict
    {'total': 32814120, 'available': 26753468, 'used': 6060652, 'used_percent': 18, 'available_percent': 82}}
    All in kbytes
    """
    info = open('/proc/meminfo', 'r').read().split('\n')
    result = {'total': '', 'available': '', 'used': '', 'used_percent': '', 'available_percent': ''}
    for row in info:
        row = row.split(' ')
        row = [x for x in row if x]
        if len(row) != 3:
            continue
        if 'MemTotal' in row[0]:
            result['total'] = int(row[1])
        if 'MemAvailable' in row[0]:
            result['available'] = int(row[1])
    result['used'] = result['total'] - result['available']
    result['used_percent'] = int(result['used'] / result['total'] * 100)
    result['available_percent'] = 100 - result['used_percent']
    return result

def _collect_nvidia_stats() -> list:
    """
        Returned list
        [
            {
                'index': '0',
                'driver_version': '440.100', 
                'name': 'Tesla T4', 
                'pci.bus_id': '00000000:AF:00.0', 
                'fan.speed': '', 
                'pstate': 'P0', 
                'memory.total': '15109', 
                'memory.used': '2003', 
                'memory.free': '13106', 
                'utilization.memory: '9', 
                'utilization.gpu': '36', 
                'utilization.gpu.enc': '21',
                'utilization.gpu.dec': '21',
                'utilization.gpu.sm': '21',
                'temperature.gpu': '45'
                'power': '34'
            }
        ]
    """
    result = []
    usage_stats = _get_nvidia_usage_stats()
    dmon_stats = _get_nvidia_dmon_stats()
    if not usage_stats or not dmon_stats:
        logger.error("nvidia usage stats or nvidia dmon stats is empty, skip stats generation")
        return result
    if usage_stats.keys() != dmon_stats.keys():
        logger.error("nvidia collect stats failed. gpus not the same in usage and dmon files")
        return result
    for gpu_id, usage in usage_stats.items():
        dmon = dmon_stats[gpu_id]
        del usage['count']
        del usage['serial']
        usage['utilization.gpu.enc'] = dmon['enc']
        usage['utilization.gpu.dec'] = dmon['dec']
        usage['utilization.gpu.sm'] = dmon['sm']
        usage['power'] = dmon['power']
        usage['index'] = gpu_id
        result.append(usage)
    return result


@celery.task
def containers_discovery():
    if not _lock(CONTAINERS_DISCOVERY_LOCK_KEY):
        logger.warning('containers discovery locked by another celery thread')
        return
    client = docker.DockerClient(base_url=DOCKER_SOCK)
    containers = []
    for container in client.containers.list(all=True):
        container_data = {
            'name': '',
            'id': '',
            'status': '',
            'last_log': '',
            'started_at': '',
            'finished_at': '',
            'finished_at_formatted': '', 
            'up': '',
            'image': '',
            'ff_wrapper': None,
            'cmd': '',
            'base_pid': '',
            'ffmpeg_pid': '',
            'created': '',
            'restart_count': '',
            'is_host_network': '',
            # metrics. All in %
            'gpu_usage_enc': '',
            'gpu_usage_dec': '',
            'gpu_usage_mem': '',
            'gpu_usage_sm': '',
            'gpu_name': '',
            'gpu_index': '',
            'gpu_bus_id': '',
            'gpu_mem': '',
            'cpu_usage': '',
        }
        is_ff_wrapper = False
        is_ffmpeg = False
        for tag in container.image.tags:
            if 'ffmpeg' in tag:
                is_ffmpeg = True
            if 'ffw-ffmpeg' in tag:
                is_ff_wrapper = True
        if not is_ffmpeg:
            continue
        container_data.update(_collect_container_data(container))
        if is_ff_wrapper and container.status == "running":    
            container_data['ff_wrapper'] = _collect_ff_wrapper_data(container)
        container_data.update(_collect_container_hw_metrics(container_data['ffmpeg_pid']))
        containers.append(container_data)
        containers.sort(key=lambda x: x['name'])
    try:
        json_data = json.dumps(containers)
        redis_con.set(CONTAINERS_DISCOVERY_DATA_KEY, json_data)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        redis_con.set(CONTAINERS_DISCOVERY_LAST_UPDATE_KEY, now)
        logger.info('Container discovery updated at {}'.format(now))
    except TypeError as e:
        logger.error("Error while trying write containers_discovery data to redis: {}".format(str(e)))
    redis_con.delete(CONTAINERS_DISCOVERY_LOCK_KEY)


def _open_csv(file_path: str) -> list:
    data = []
    if not os.path.exists(file_path):
        logger.warning(f"{file_path} doesn't exists")
        return data
    try:
        with open(file_path, 'r') as f:
            try: 
                reader = csv.DictReader(f)
                result = []
                for row in reader:
                    result.append({k.strip(): v.strip() for k, v in row.items()})
                return result
            except csv.Error:
                logger.warning(f"Error while parse {file_path} to csv")
    except IOError:
        logger.warning(f"Error while open {file_path}")
        logger.debug(traceback.format_exc())
        return data


def _open_file(file_path: str) -> list:
    try:
        with open(file_path, 'r') as f:
            return f.readlines()
    except IOError:
        logger.warning(f'Error while open file {file_path}')
        logger.debug(traceback.format_exc())
        return []


def _get_nvidia_usage_stats() -> dict:
    """
    Returned dict:        
    {'0': 
        {'driver_version': '440.100', 
        'count': '1', 
        'name': 'Tesla T4', 
        'serial': '1325219083788', 
        'uuid': 'GPU-bbd3f1b1-660a-44b0-911f-169e11579607', 
        'pci.bus_id': '00000000:AF:00.0', 
        'fan.speed': '', 
        'pstate': 'P0', 
        'memory.total': '15109', 
        'memory.used': '2003', 
        'memory.free': '13106', 
        'utilization.memory: '9', 
        'utilization.gpu': '36', 
        'temperature.gpu': '45'
        }
    }

    """
    file_path = os.path.join(NVIDIA_STATS_DIR, 'usage')
    data = _open_csv(file_path)
    if not data:
        logger.error("Error while opening nvidia usage stats")
        return {}
    result = {}
    for row in data:
        if len(row.keys()) != 15:
            logger.warning(f"Warning. Wrong format nvidia usage file, skip (row)")
            continue
        index = row['index']
        del row['index']
        row = {k.split(' ')[0]: v for k,v in row.items()}
        row['memory.total'] = row['memory.total'].split(' ')[0]
        row['memory.used'] = row['memory.used'].split(' ')[0]
        row['memory.free'] = row['memory.free'].split(' ')[0]
        row['utilization.memory'] = row['utilization.memory'].split(' ')[0]
        row['utilization.gpu'] = row['utilization.gpu'].split(' ')[0]
        if row['fan.speed'] == '[N/A]':
            row['fan.speed'] = ''
        result[index] = row
    return result 


def _get_nvidia_compute_stats(ffmpeg_pid: str) -> dict:
    """
    Returned dict
    {
        'timestamp': '2020/10/27 19:41:10.301', 
        'gpu_name': 'Tesla T4', 
        'gpu_bus_id': '00000000:AF:00.0', 
        'pid': '47485', 
        'process_name': '/usr/local/bin/ffmpeg', 
        'used_gpu_memory': '1227 MiB'}
    """
    file_path = os.path.join(NVIDIA_STATS_DIR, 'compute_query')
    data = _open_csv(file_path)
    if not data:
        logger.error("Error while opening nvidia compute query stats")
        return {}
    for row in data:
        if row.get('pid') == ffmpeg_pid:
            if len(row.keys()) != 6:
                logger.warning(f"Warning. Wring nvidia compute stats file format ({row}")
                return {}
            row = {k.split(' ')[0]: v for k, v in row.items()}
            return row
    return {}


def _get_nvidia_pmon_stats(ffmpeg_pid: str) -> dict:
    """
    Returned dict
    {
        'gpu_index': '0', 
        'pid': '47485', 
        'type': 'C', 
        'sm': '34', 
        'mem': '7', 
        'enc': '23', 
        'dec': '2', 
        'command': 'ffmpeg'
    }
    """
    file_path = os.path.join(NVIDIA_STATS_DIR, 'pmon')
    data = {}
    raw_data = _open_file(file_path)
    if not raw_data or len(raw_data) < 3:
        logger.error("Error while opening nvidia pmon stats, source is empty")
        return data
    raw_data = raw_data[2:]
    for row in raw_data:
        if not row:
            continue
        row = row.split(' ')
        row = [x.strip() for x in row if x.strip()] 
        # format -  gpu pid type sm mem enc dec command
        if len(row) != 8:
            logger.warning(f'Error while parsing nvidia pmon. Number of elements != 8 (wrong format). Src: {row}')
            return data
        row = {'gpu_index': row[0], 'pid': row[1], 'type': row[2],
                'sm': row[3], 'mem': row[4], 'enc': row[5], 
                'dec': row[6], 'command': row[7]
              }
        if ffmpeg_pid and row['pid'] == ffmpeg_pid:
            return row
    return data

def _get_nvidia_dmon_stats() -> dict:
    """
        Returned dict
        {'0': 
            {'power': '34', 
            'gtemp': '44', 
            'mtemp': '-', 
            'sm': '36', 
            'mem': '8', 
            'enc': '51', 
            'dec': '10', 
            'mclk': '5000', 
            'pclk': '810'
            }
        }
    """
    file_path = os.path.join(NVIDIA_STATS_DIR, 'dmon')
    # '{'gpu_index': {'power':'', ...}
    data = {}
    raw_data = _open_file(file_path)
    if not raw_data or len(raw_data) < 3:
        logger.error("Error while opening nvidia dmon stats, source is empty")
        return data
    raw_data = raw_data[2:]
    for row in raw_data:
        if not row:
            continue
        row = row.split(' ')
        row = [x.strip() for x in row if x.strip()] 
        # format -  gpu   pwr gtemp mtemp    sm   mem   enc   dec  mclk  pclk
        if len(row) != 10:
            logger.warning(f'Error while parsing nvidia dmon. Number of elements != 10 (wrong format). Src: {row}')
            return data
        gpu_index = row[0]
        data[gpu_index] = {'power': row[1], 'gtemp': row[2],
                'mtemp': row[3], 'sm': row[4], 'mem': row[5], 
                'enc': row[6], 'dec': row[7], 'mclk': row[8], 'pclk': row[9]
              }
    return data


def _collect_container_hw_metrics(ffmpeg_pid: str) -> dict:
    data = {}
    if not os.path.exists(NVIDIA_STATS_DIR):
        return data
    # enc dec mem sm
    pmon = _get_nvidia_pmon_stats(ffmpeg_pid)
    # timestamp gpu_name gpu_bus_id pid process_name used_gpu_memory
    compute_stats = _get_nvidia_compute_stats(ffmpeg_pid)
    data = {'gpu_usage_enc': pmon.get('enc'), 
            'gpu_usage_dec': pmon.get('dec'),
            'gpu_usage_mem': pmon.get('mem'),
            'gpu_usage_sm': pmon.get('sm'),
            'gpu_index': pmon.get('gpu_index'),
            'gpu_name': compute_stats.get('gpu_name'),
            'gpu_bus_id': compute_stats.get('gpu_bus_id'),
            'gpu_mem': compute_stats.get('used_gpu_memory'),
    }
    if data['gpu_mem']:
        data['gpu_mem'] = data['gpu_mem'].split(' ')[0]
    return data


def _get_ffmpeg_process_data(container: docker.models.containers.Container) -> (str, str):
    """
    returned pid, cpu usage
    """
    top = []
    empty_result = '', ''
    if container.status != 'running':
        return empty_result
    try:
        # [ (pid, cmd), (pid, cmd), .. ]
        top = container.top(ps_args='-eo pid,comm,pcpu')
    except docker.errors.APIError:
        logger.error("Error while trying get container top.\n" + traceback.format_exc())
        return empty_result
    if not top or 'Processes' not in top:
        logger.warning(f"Warning. Top is empty  or format is wrong. container:'{container.name}', top: {top}")
        return empty_result
    try:
        top = top['Processes']
        for pid, cmd, pcpu in top:
            if 'ffmpeg' in cmd:
                return pid, pcpu
        return empty_result
    except ValueError:
        logger.warning(f"Warning. Format of top is wrong.container:'{container.name}', top: {top}")
        logger.warning(traceback.format_exc())
        return empty_result

def _collect_container_data(container: docker.models.containers.Container) -> dict:
    data = {}
    data['id'] = container.id
    data['name'] = container.name
    if len(container.image.tags) > 0:
        data['image'] = container.image.tags[0]
    data['started_at'] = container.attrs['State']['StartedAt']
    data['finished_at'] = container.attrs['State']['FinishedAt']
    data['finished_at_formatted'] = data['finished_at'].replace('T', ' ')
    data['finished_at_formatted'] = ' '.join(data['finished_at_formatted'].split('.')[:-1])
    data['cmd'] = ' '.join(container.attrs['Args'])
    data['base_pid'] = container.attrs['State']['Pid']
    pid, pcpu = _get_ffmpeg_process_data(container)
    data['ffmpeg_pid'] = pid
    data['cpu_usage'] = pcpu
    if container.status == "running":
        now =  datetime.datetime.now(pytz.timezone("UTC")).replace(tzinfo=None)
        started = _parse_docker_dt(data['started_at'])
        up = now - started
        hours = up.seconds // 3600
        minutes = (up.seconds % 3600) // 60
        seconds = up.seconds % 60
        data['up'] = '{}d:{}h:{}m:{}s'.format(up.days, hours, minutes, seconds)
    data['status'] = container.status
    if container.status == "running":
        try:
            data['last_log'] = container.logs(tail=LAST_DOCKER_LOGS_COUNT, timestamps=True)
            data['last_log'] = data['last_log'].decode('utf-8')
        except docker.errors.APIError:
            logger.error(traceback.format_exc())
    data['restart_count'] = container.attrs['RestartCount']
    data['created'] = container.attrs['Created']
    data['is_host_network'] = False
    networks = container.attrs['NetworkSettings'].get('Networks')
    if networks and 'host' in networks:
        data['is_host_network'] = True
    return data

def _collect_ff_wrapper_data(container: docker.models.containers.Container) -> dict:
    data = {}
    cmd = 'sh -c \'cd {} && for i in `ls -1`; do echo "$i `cat $i`"; done\''
    status_files = _container_exec(container, cmd.format(os.path.join(DEFAULT_WORKDIR, 'status/')))
    if not status_files:
        logger.error('Container {} has no status files in {}'.format(
            container.name, os.path.join(DEFAULT_WORKDIR, 'status'))
        )
        return
    status_files = status_files.split('\n')
    for line in status_files:
        status = line.split(' ')
        if len(status) != 2:
            continue
        status, value = status
        data[status] = value
    return data

def _container_exec(container: docker.models.containers.Container, cmd: str) -> str:
    exit_code, value = container.exec_run(cmd)
    value = value.decode('utf-8').strip()
    if exit_code:
        logger.error("Error. CMD: {} ; Output: {}".format(cmd, value))
        return ''
    return value

            
