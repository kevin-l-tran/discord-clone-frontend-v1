import certifi

from flask import Flask, current_app
from mongoengine import connect, disconnect, get_connection
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

flask_bcrypt = Bcrypt()
jwt = JWTManager()
gcreds = None

load_dotenv()


def create_app(config_object="config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    with app.app_context():
        try:
            connect(
                db=current_app.config['MONGO_DB'],
                host=current_app.config['MONGO_HOST'],
                port=current_app.config['MONGO_PORT'],
                serverSelectionTimeoutMS=5000,
                tls=True,
                tlsCAFile=certifi.where(),
            )
            client = get_connection()
            client.admin.command('ping')
            app.logger.info("✅ MongoDB connection established")
        except (ServerSelectionTimeoutError, ConfigurationError) as exc:
            app.logger.critical("❌ MongoDB connection failed: %s", exc)
            disconnect()
            raise

    from .auth import auth

    app.register_blueprint(auth, urlprefix='/')

    flask_bcrypt.init_app(app)
    jwt.init_app(app)

    return app
