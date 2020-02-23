import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_dropzone import Dropzone
from flask_wtf.csrf import CsrfProtect
from flask_mail import Mail
from werkzeug.debug import DebuggedApplication

from celery import Celery

import config
from . import custom_filters

app = Flask(__name__)
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

app.config.from_object(os.environ.get('FLASK_ENV') or 'config.DevelopementConfig')
custom_filters.generate_custom_filter(app)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://redis:6379/0',
        broker='amqp://myuser1:mypass1@rabbitmq:5672/myvhost1',
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery_app = make_celery(app)

csrf = CsrfProtect()
csrf.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app,  db)

mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

dropzone = Dropzone(app)

from . import views
