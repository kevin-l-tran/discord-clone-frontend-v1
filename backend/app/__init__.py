from flask import Flask, current_app
from mongoengine import connect
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
        connect(
            db=current_app.config['MONGO_DB'],
            host=current_app.config['MONGO_HOST'],
            port=current_app.config['MONGO_PORT'],
        )

        flask_bcrypt.init_app(app)
        jwt.init_app(app)

    return app
