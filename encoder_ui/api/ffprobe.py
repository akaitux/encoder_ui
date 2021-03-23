import subprocess
import json


class FFProbe:

    def __init__(self):
        self.bin = 'ffprobe'

    def exec(self, cmd: str) -> str:
        p = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        is_error = False
        stdout, _ = p.communicate()
        if stdout:
            stdout = stdout.decode('utf-8')
        if p.returncode != 0:
            is_error = 1
        return {'stdout': stdout, 'is_error': is_error}

    def get_streams(self, addr: str) -> (dict, str):
        """
        :param addr - address of stream
        :returned dict - dict with streams
        :returned str - stderr if not empty or if json parse error
        """
        error_msg = 'Error when probe stream {}'.format(addr)
        cmd = '{} -loglevel quiet -hide_banner -print_format json -show_streams -show_programs {}'.format(self.bin, addr)
        output = self.exec(cmd) 
        if output.get('is_error'):
            return None, '{}'.format(error_msg)
        try:
            return json.loads(output.get('stdout')), None
        except json.decoder.JSONDecodeError:
            return None, '{} json is not valid (cmd: {}, output: {})'.format(error_msg, cmd, output)
        except Exception as e:
            return None, '{} {} (cmd: {}, output: {})'.format(error_msg, str(e), cmd, output)
