# Setup log for the whole app
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_migrate import Migrate, command

from src.config import DevelopmentConfig, StagingConfig, ProductionConfig, Config
from .celery_app import celery_init_app

# Initialize Flask app and set config
app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Config is PROD by default
if os.environ['CONFIG'] == 'DEV':
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)

ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mov', 'mpeg'}
# Set CORS config
CORS(app=app, origins=app.config['CORS_ORIGIN'], supports_credentials=True)

# Set configuration for DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db, command='migrate')


# Function to run migrations
def run_migrations():
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()


# upgrade database
if os.environ['CONFIG'] != 'DEV':
    run_migrations()


# Set JWT Config
jwt = JWTManager(app)

"""Setting up celery config
broker_url: Sets the broker URL for Celery, which is used for communication
between the Flask app and the Celery worker.

result_backend: Specifies the result backend to be used, with "rpc://"
indicating the use of RPC (Remote Procedure Call) as the result backend.

task_ignore_result: Controls whether the Flask app should ignore the
results of Celery tasks or not. Setting it to False ensures that task
results are not ignored
"""
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")
broker_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
app.config.from_mapping(
    CELERY=dict(
        broker_url=broker_url,
        result_backend=broker_url,
        task_ignore_result=True,
    ),
)

celery_init_app(app)
celery_app = app.extensions["celery"]

# firebase_credentials = {
#     "type": app.config['GOOGLE_FCM_TYPE'],
#     "project_id": app.config['GOOGLE_FCM_PROJECT_ID'],
#     "private_key_id": app.config['GOOGLE_FCM_PRIVATE_KEY_ID'],
#     "private_key": app.config['GOOGLE_FCM_PRIVATE_KEY'].replace(r"\n", "\n"),
#     "client_email": app.config['GOOGLE_FCM_CLIENT_EMAIL'],
#     "client_id": app.config['GOOGLE_FCM_CLIENT_ID'],
#     "auth_uri": app.config['GOOGLE_FCM_AUTH_URI'],
#     "token_uri": app.config['GOOGLE_FCM_TOKEN_URI'],
#     "auth_provider_x509_cert_url": app.config['GOOGLE_FCM_AUTH_PROVIDER_X509_CERT_URL'],
#     "client_x509_cert_url": app.config['GOOGLE_FCM_CLIENT_X509_CERT_URL']
# }

# cred = credentials.Certificate(firebase_credentials)
# firebase_app = firebase_admin.initialize_app(credential=cred)

from src import routes
app.config['SWAGGER_DEFAULT_MODELS_EXPANSION_DEPTH'] = -1