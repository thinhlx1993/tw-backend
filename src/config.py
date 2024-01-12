import os
from sqlalchemy.pool import NullPool

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
    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URI"]
    SQLALCHEMY_ECHO=False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool
    }
    CORS_ORIGIN = os.environ['CORS_ORIGIN']
    UPLOAD_FOLDER = os.environ['UPLOAD_FOLDER']
    SENTRY_CONFIG = os.environ['SENTRY_CONFIG']
    PROTOTYPE_SCHEMA = 'cs_cognicept'
    PUBLIC_SCHEMA_TABLES = ['user', 'organization', 'user_organization_mapping',
                            'user_notification_token', 'agent', 'user_password_reset_token', 'access_keys']
    GET_SCHEMAS_QUERY = "select schema_name from information_schema.schemata WHERE schema_name NOT LIKE 'pg_%%' and schema_name LIKE 'cs_%%' "
    GET_INDIVIDUAL_SCHEMA_QUERY = "select schema_name from information_schema.schemata WHERE schema_name LIKE 'cs_"
    GET_ALL_SCHEMAS_QUERY = "select schema_name from information_schema.schemata WHERE schema_name NOT LIKE 'pg_%%' and schema_name LIKE 'cs_%%' "
    TOKEN_SALT = os.environ['TOKEN_SALT']
    API_URL = os.environ['API_URL']
    BASE_URL = os.environ['BASE_URL']
    SUPER_ADMIN = os.environ['SUPER_ADMIN']


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
