from flask import Blueprint
import json
import copy
import logging
import traceback
import requests
import os
from config import settings
from flask.blueprints import Blueprint
from flask import current_app
from flask import request
from encoder_ui.api.ffprobe import FFProbe
from encoder_ui.api.funcs import (
    _get_containers,
    _get_resources,
    _find_container_logs_dir,
    _get_container_log_files,
    _is_addr_valid,
    _filter_ffprobe_streams,
    _get_file_path,
)
from encoder_ui.api.ff_presets_funcs import compile_ff_preset


app = Blueprint('api', __name__)


logger = logging.getLogger('flask')
logger.propagate = True


@app.route('/api/containers/')
def get_containers():
    """
    GET param: only_ffw - only ff_wrapper containers
    """
    only_ffw = False
    if 'only_ffw' in request.args:
        only_ffw = True
    try:
        containers, dt = _get_containers(only_ffw=only_ffw)
        data = {'containers': containers, 'updated_at': dt.strftime('%Y-%m-%d %H:%M:%S')}
        return '{}'.format(json.dumps(data))
    except TypeError as e:
        current_app.logger.error(str(e))
        return json.dumps({'error': str(e)}), 500
    except ValueError as e:
        current_app.logger.error(str(e))
        return json.dumps({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error('{}\n{}'.format(str(e), traceback.format_exc()))
        return json.dumps({'error': 'Undefined exception'}), 500


@app.route('/api/resources/')
def get_resources():
    try:
        resources, dt = _get_resources()
        data = {'resources': resources, 'updated_at': dt.strftime('%Y-%m-%d %H:%M:%S')}
        return '{}'.format(json.dumps(data))
    except TypeError as e:
        current_app.logger.error(str(e))
        return json.dumps({'error': str(e)}), 500
    except ValueError as e:
        current_app.logger.error(str(e))
        return json.dumps({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error('{}\n{}'.format(str(e), traceback.format_exc()))
        return json.dumps({'error': 'Undefined exception'}), 500


@app.route('/api/logs/<string:container_name>/')
def get_container_logs_list(container_name: str):
    if not container_name:
        err = f"Container name is empty"
        return json.dumps({'error': err}), 400
    if not os.path.exists(settings.LOGS_PATH):
        err = f"Logs directory doesn't exists ({settings.LOGS_PATH})"
        return json.dumps({'error': err}), 500
    logs_path = _find_container_logs_dir(container_name)
    if not logs_path :
        err = "Container logs dir not found"
        return json.dumps({'error': err}), 404
    files = _get_container_log_files(logs_path)
    return json.dumps(files)


@app.route('/api/logs/<string:container_name>/<string:file_name>/')
def get_container_log_file(container_name:str, file_name:str):
    if not file_name.startswith('ffmpeg_') and not file_name.startswith('manager_'):
        err = f"Wrong file name, must be started with ffmpeg_ or manager_"
        return json.dumps({'error': err}), 400
    if not container_name:
        err = f"Container name is empty"
        return json.dumps({'error': err}), 400
    if not file_name:
        err = f"Filename is empty"
        return json.dumps({'error': err}), 400
    logs_path = _find_container_logs_dir(container_name)
    if not logs_path :
        err = "container logs dir not found"
        return json.dumps({'error': err}), 404
    files = _get_container_log_files(logs_path)
    if not files:
        err = "File not found"
        return json.dumps({'error': err}), 404
    file_path = _get_file_path(logs_path, files, file_name)
    if not file_path:
        err = "File not found"
        return json.dumps({'error': err}), 404
    try:
        content = open(file_path, 'r').read()
        result = {'content': content}
        return json.dumps(result)
    except FileNotFoundError:
        err = "File not found"
        return json.dumps({'error': err}), 404
    except OSError:
        err = "Access denied"
        return json.dumps({'error': err}), 500


@app.route('/api/ffprobe/', methods=['POST'])
def ffprobe_info():
    """
    POST param: addr - address of stream
    """
    addr = request.values.get('addr')
    if not addr:
        err = "addr required in POST params"
        return json.dumps({'error': err}), 500
    if not _is_addr_valid(addr):
        err = "addr not valid"
        return json.dumps({'error': err}), 400
    ffprobe = FFProbe()
    result, err = ffprobe.get_streams(addr)
    if not err:
        return json.dumps(_filter_ffprobe_streams(result))
    else:
        return json.dumps({'error': err}), 500
    

@app.route('/api/ff_presets/compile/', methods=['POST'])
def ff_presets_compile():
    template = request.values.get('template')
    print(template)
    if not template:
        err = "template required in POST params"
        return json.dumps({'errors': [err, ]}), 400
    try:
        template = json.loads(template)
    except ValueError:
        err = "not valid json"
        return json.dumps({'errors': [err,]}), 400
    stream, err = compile_ff_preset(template)
    if not err:
        return json.dumps({'cmd': stream.cmd}, ensure_ascii=False), 200
    else:
        return json.dumps({'errors': err}, ensure_ascii=False), 400

