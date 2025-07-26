import datetime
import os

class BaseConfig:
    SECRET_KEY               = os.environ.get("SECRET_KEY", "temporary key")

    FRONTEND_URL             = os.environ.get("FRONTEND_URL")

    MONGO_DB                 = os.getenv("MONGO_DB", "project_db")
    MONGO_HOST               = os.getenv("MONGO_HOST", "localhost"),
    MONGO_PORT               = int(os.getenv("MONGO_PORT", 27017))

    JWT_SECRET_KEY           = os.getenv("JWT_SECRET_KEY", "temporary key")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)

    G_SECRETS_FILE           = os.getenv("G_SECRETS_FILE")
    G_REDIRECT_URI           = os.getenv("G_REDIRECT_URI", "http://localhost:5000/calendar/callback")
    G_SCOPES                 = ["https://www.googleapis.com/auth/calendar"]

    NINJA_API_KEY            = os.getenv("NINJA_API_KEY")

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
