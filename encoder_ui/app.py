from flask import Flask
from werkzeug.debug import DebuggedApplication
from celery import Celery
from encoder_ui.api import blueprint_api
from encoder_ui.web import blueprint_web


CELERY_TASK_LIST = [
    'encoder_ui.celery.discovery.tasks'
]

def create_celery_app(app=None):
    app = app or create_app()

    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASK_LIST)
    celery.conf.update(app.config)

    return celery


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.
    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, static_folder='web/static', template_folder='web/templates', static_url_path='')

    app.config.from_object('config.settings')

    if settings_override:
        app.config.update(settings_override)
    
    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
    app.register_blueprint(blueprint_api)
    app.register_blueprint(blueprint_web)
    return app
