# Setup log for the whole app
import os
from alembic import command
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_script import Manager
from flask_caching import Cache
from flask_migrate import Migrate, MigrateCommand
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .config import DevelopmentConfig, StagingConfig, ProductionConfig, Config

# Initialize Flask app and set config
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# sentry_sdk.init(
#     dsn=Config.SENTRY_CONFIG,
#     integrations=[FlaskIntegration(), SqlalchemyIntegration()],
#     traces_sample_rate=1.0
# )

# Config is PROD by default
if os.environ['CONFIG'] == 'DEV':
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)


# Set CORS config
CORS(app=app, origins=app.config['CORS_ORIGIN'], supports_credentials=True)

# Set configuration for DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db, compare_type=True)

if os.environ['CONFIG'] == 'PROD':
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    with app.app_context():
        command.upgrade(migrate.get_config(), 'head')

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

from src import routes

app.config['SWAGGER_DEFAULT_MODELS_EXPANSION_DEPTH'] = -1
