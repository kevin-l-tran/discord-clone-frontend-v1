from mongoengine import Document, StringField, EmailField, ValidationError

from . import flask_bcrypt


class User(Document):
    name = StringField(required=True, unique=True, min_length=4)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True, min_length=60)

    def set_password(self, password: str):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        self.password_hash = flask_bcrypt.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    meta = {
        "indexes": [
            {
                "fields": ["username"],
                "unique": True,
                "collation": {"locale": "en", "strength": 2},
            },
            {
                "fields": ["email"],
                "unique": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ]
    }
