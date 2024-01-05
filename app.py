from Social.src.blueprints.AuthenticationBlueprint import auth_app
# from Social.src.blueprints.RequestSummaryBlueprint import summary_app
from Social.src.blueprints.UserBlueprint import user_app
from Social.src.blueprints.StatesBlueprint import states_app
from Social.src.blueprints.PlatformBlueprint import platform_app
from Social.src.blueprints.ElectionsBlueprint import elections_app
from Social.src.blueprints.PoliticiansBlueprint import politicians_app
from Social.src.blueprints.PagesBlueprint import pages_app
from Social.src.blueprints.FacebookBlueprint import facebook_app
from logging.config import dictConfig
from flask_cors import CORS
from flask_migrate import Migrate
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
from waitress import serve
from flask_jwt_extended import JWTManager
from Social.src.utils.models import db
from Social.src.utils.response import Response
from Social.src.utils.custom_json_encoder import CustomJSONEncoder
from Social.src.configurations.settings import DB_FILE, ENABLE_CORS,PostgreSQL_Connection
from Social.src.utils.helpers import bootstrap_data
import os
import datetime
import json
import logging.handlers
import anticrlf


dictConfig({
    'version': 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s)) Log : %(message)s",
            "datefmt": "%d-%m-%Y %I:%M:%S",
            "()": 'anticrlf.LogFormatter'
        }
    },
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    },
        'file.handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': './logs/app.log',
            'maxBytes': 10000,
            'backupCount': 10,
            'level': 'DEBUG',
            'formatter': 'default'
        }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi', 'file.handler']
    }
})

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Enabling CORS on flask level, to be used in development only
if ENABLE_CORS:
    CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SQLALCHEMY_DATABASE_URI"] = DB_FILE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Enabling Migration
migrate = Migrate(app, db, render_as_batch=True)

# Enabling JWT for application
jwt = JWTManager(app)

# Logging Handler
handler = logging.handlers.RotatingFileHandler('./logs/console.log', maxBytes=1024 * 1024, backupCount=10)
handler.setFormatter(anticrlf.LogFormatter(
    "%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s)) Log : %(message)s"))
app.logger.setLevel(logging.INFO)
app.logger.addHandler(handler)

app.config['JSON_AS_ASCII'] = False

# Registering Blueprints
app.register_blueprint(auth_app, url_prefix='/api/')
app.register_blueprint(elections_app, url_prefix='/api/elections/')
app.register_blueprint(user_app, url_prefix='/api/user/')
app.register_blueprint(states_app, url_prefix='/api/states/')
app.register_blueprint(platform_app, url_prefix='/api/platform/')
app.register_blueprint(politicians_app, url_prefix='/api/politician/')
app.register_blueprint(pages_app, url_prefix='/api/pages/')
app.register_blueprint(facebook_app, url_prefix='/api/facebook/')

app.secret_key = os.urandom(12)


@app.route('/api/health', methods=['GET', 'POST'])
def index():
    return json.dumps(Response(status=True, message="Social Analytics Backend Services are UP!", data={}).__dict__,
                      cls=CustomJSONEncoder)


with app.app_context():
    bootstrap_data()

# base_path = r"D:\AISAL\Repo\PoliticalEngagement\src\assets\img\politicians\haryana"
# files = os.listdir(base_path)
# for i in files:
#     os.rename(os.path.join(base_path, i), os.path.join(base_path, i.lower().replace(" ", "_")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    # serve(app, host="0.0.0.0", port=8080)
