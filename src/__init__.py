# Setup log for the whole app
import os
from alembic import command
from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_script import Manager
from flask_caching import Cache
from flask_migrate import Migrate, MigrateCommand
from flask_executor import Executor

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .config import DevelopmentConfig, StagingConfig, ProductionConfig, Config

# Initialize Flask app and set config
app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Config is PROD by default
if os.environ["CONFIG"] == "DEV":
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)
    sentry_sdk.init(
        dsn="https://4d71513c1fe88390e864983b9110f431@o1068161.ingest.sentry.io/4506666720952320",
        enable_tracing=True,
        traces_sample_rate=0.3,  # Adjust sample rate as needed,
        integrations=[
            FlaskIntegration(
                transaction_style="url",
            ),
        ],
    )
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

# Set CORS config
CORS(app=app, origins=app.config["CORS_ORIGIN"], supports_credentials=True)

# Set configuration for DB
db = SQLAlchemy(app)
executor = Executor(app)
migrate = Migrate(app, db, compare_type=True)

if os.environ["CONFIG"] == "PROD":
    manager = Manager(app)
    manager.add_command("db", MigrateCommand)
    with app.app_context():
        command.upgrade(migrate.get_config(), "head")

# Set JWT Config
jwt = JWTManager(app)


# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["50/second"],
#     storage_uri="memory://",
# )


from src import routes

app.config["SWAGGER_DEFAULT_MODELS_EXPANSION_DEPTH"] = -1
