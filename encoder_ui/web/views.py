from flask import Blueprint
from flask import current_app, request, render_template


app = Blueprint('web', __name__)


@app.route('/')
def index():
     return render_template('index.html')

@app.route('/logs/ff_wrapper/<string:container_name>/')
def container_logs(container_name):
     return render_template('ff_wrapper_logs.html')

@app.route('/logs/ff_wrapper/<string:container_name>/<string:file_name>/')
def container_log_file(container_name, file_name):
     return render_template('ff_wrapper_log_file.html')

@app.route('/ffprobe/')
def ffprobe():
     return render_template('ffprobe.html')


