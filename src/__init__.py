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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .config import DevelopmentConfig, StagingConfig, ProductionConfig, Config

# Initialize Flask app and set config
app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# sentry_sdk.init(
#     dsn=Config.SENTRY_CONFIG,
#     integrations=[FlaskIntegration(), SqlalchemyIntegration()],
#     traces_sample_rate=1.0
# )

# Config is PROD by default
if os.environ["CONFIG"] == "DEV":
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)


# Set CORS config
CORS(app=app, origins=app.config["CORS_ORIGIN"], supports_credentials=True)

# Set configuration for DB
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db, compare_type=True)

if os.environ["CONFIG"] == "PROD":
    manager = Manager(app)
    manager.add_command("db", MigrateCommand)
    with app.app_context():
        command.upgrade(migrate.get_config(), "head")

# Set JWT Config
jwt = JWTManager(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)


from src import routes

app.config["SWAGGER_DEFAULT_MODELS_EXPANSION_DEPTH"] = -1
