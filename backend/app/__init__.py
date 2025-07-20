import os

from flask import Flask
from flask_mongoengine import MongoEngine
from dotenv import load_dotenv

load_dotenv()

db = MongoEngine()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'temporary key')
    
    app.config['MONGODB_SETTINGS'] = {
        'db':       os.getenv('MONGO_DB', 'my_database'),
        'host':     os.getenv('MONGO_HOST', 'localhost'),
        'port':     int(os.getenv('MONGO_PORT', 27017)),
    }

    db.init_app(app)
    return app