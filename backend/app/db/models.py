from datetime import datetime, timezone
from enum import Enum
from mongoengine import (
    Document,
    StringField,
    EmailField,
    ValidationError,
    URLField,
    ReferenceField,
    ListField,
    CASCADE,
    DateTimeField,
    BooleanField,
    IntField,
    LazyReferenceField,
    QuerySet,
    EnumField,
)

from .. import flask_bcrypt


class TimestampedDocument(Document):
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    meta = {"abstract": True}


class User(TimestampedDocument):
    username = StringField(required=True, unique=True, min_length=4)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True, min_length=60)

    def set_password(self, password: str):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        self.password_hash = flask_bcrypt.generate_password_hash(password).decode(
            "utf-8"
        )

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

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username
        }


# GROUP #########################################################################


class Group(TimestampedDocument):
    name = StringField(required=True, min_length=4)
    description = StringField(max_length=150, null=True)
    img_path = StringField(required=True)


class RoleType(Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    MEMBER = "Member"


class GroupMembership(TimestampedDocument):
    user = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    group = LazyReferenceField(Group, required=True, reverse_delete_rule=CASCADE)
    nickname = StringField()
    role = EnumField(RoleType, default=RoleType.MEMBER)
    is_muted = BooleanField(default=False)
    is_banned = BooleanField(default=False)

    meta = {"indexes": [{"fields": ["user", "group"], "unique": True}]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "user": str(self.user.id),
            "group": str(self.group.id),
            "nickname": self.nickname,
            "role": self.role.value,
            "is_muted": self.is_muted,
            "is_banned": self.is_banned,
            "created_at": self.created_at.isoformat(),
        }


# END ###########################################################################

# CHANNEL #######################################################################


class ChannelType(Enum):
    TEXT = "text"
    VOICE = "voice"


class Channel(Document):
    group = ReferenceField(Group, required=True, reverse_delete_rule=CASCADE)
    name = StringField(required=True)
    type = EnumField(ChannelType, default=ChannelType.TEXT)
    topic = StringField()
    position = IntField(default=0)

    meta = {"indexes": [{"fields": ["group", "name"], "unique": True}]}

    def to_dict(self):
        return {
            "id": str(self.id),
            "group": str(self.group.id),
            "name": self.name,
            "type": self.type.value,
            "topic": self.topic,
            "position": self.position,
        }


# END ###########################################################################

# MESSAGE #######################################################################


class MessageQuerySet(QuerySet):
    def delete(self):  # soft‑delete: mark deleted_at and flag, don’t remove
        return super().update(
            deleted_at=lambda: datetime.now(timezone.utc), is_deleted=True
        )

    def hard_delete(self):  # truly delete documents
        return super().delete()


class Message(TimestampedDocument):
    channel = ReferenceField(Channel, required=True, reverse_delete_rule=CASCADE)
    author = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    content = StringField()
    attachments = ListField(StringField())
    edited_at = DateTimeField()
    deleted_at = DateTimeField()
    is_deleted = BooleanField(default=False)
    reply_to = ReferenceField("self", reverse_delete_rule=CASCADE)

    meta = {
        "queryset_class": MessageQuerySet,
        "indexes": [
            {
                "fields": ["reply_to"],
                "sparse": True,
            },
            "-created_at",
            "channel",
            "is_deleted",
        ],
    }

    def to_dict(self):
        base = {
            "id": str(self.id),
            "channel": str(self.channel.id),
            "author": str(self.author.id),
            "content": self.content,
            "attachments": self.attachments,
            "edited_at": self.edited_at.date().isoformat() if self.edited_at else None,
            "deleted_at": self.deleted_at.date().isoformat() if self.deleted_at else None,
            "is_deleted": self.is_deleted,
            "reply_to": str(self.reply_to.id) if self.reply_to else None,
        }
        if self.is_deleted:
            base.update(content="This message was deleted.", attachments=[])
        return base


# END ###########################################################################
