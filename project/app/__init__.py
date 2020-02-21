import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_dropzone import Dropzone
from flask_wtf.csrf import CsrfProtect
from werkzeug.debug import DebuggedApplication

import config
from . import custom_filters

app = Flask(__name__)
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

app.config.from_object(os.environ.get('FLASK_ENV') or 'config.DevelopementConfig')
custom_filters.generate_custom_filter(app)

csrf = CsrfProtect()
csrf.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app,  db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

dropzone = Dropzone(app)

from . import views
