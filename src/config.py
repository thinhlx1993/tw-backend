import os

from flask.cli import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()


class Config:
    """
    Config class for Flask App
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    PORT = os.environ["PORT"]
    JWT_SECRET_KEY = os.environ['JWT_KEY']
    MFA_SECRET_KEY = os.environ['MFA_SECRET_KEY']
    JWT_ACCESS_TOKEN_EXPIRES = 604800  # 7 days in seconds
    JWT_REFRESH_TOKEN_EXPIRES = 2592000 #30 days in seconds
    JWT_BLACKLIST_ENABLED = True
    JWT_CLAIMS_IN_REFRESH_TOKEN = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access"]
    JWT_TOKEN_LOCATION = ["headers"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URI"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO=False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool
    }
    PROTOTYPE_SCHEMA = 'default'
    CORS_ORIGIN = os.environ['CORS_ORIGIN']
    UPLOAD_FOLDER = os.environ['UPLOAD_FOLDER']
    TOKEN_SALT = os.environ['TOKEN_SALT']

    API_URL = os.environ['API_URL']


class ProductionConfig(Config):
    """
    Production Config class for Flask App
    """
    ENV = "production"
    PROPAGATE_EXCEPTIONS = True
    SQLALCHEMY_ECHO = False
    DEBUG = False


class StagingConfig(Config):
    """
    Staging Config class for Flask App
    """
    ENV = "staging"
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """
    Development Config class for Flask App
    """
    ENV = "development"
    DEVELOPMENT = True
    DEBUG = True
