import datetime
import os

class BaseConfig:
    SECRET_KEY               = os.environ.get("SECRET_KEY", "temporary key")

    MONGO_DB                 = os.getenv("MONGO_DB", "project_db")
    MONGO_HOST               = os.getenv("MONGO_HOST", "localhost"),
    MONGO_PORT               = int(os.getenv("MONGO_PORT", 27017))

    JWT_SECRET_KEY           = os.getenv("JWT_SECRET_KEY", "temporary key")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)

    G_CALLBACK_URL           = os.environ.get("G_CALLBACK_URL")
    G_API_CLIENT_ID          = os.environ.get("G_API_CLIENT_ID")
    G_API_CLIENT_SECRET      = os.environ.get("G_API_CLIENT_SECRET")
    G_SCOPES                 = ["https://www.googleapis.com/auth/calendar"]

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
