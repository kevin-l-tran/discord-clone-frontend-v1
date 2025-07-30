from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from google.cloud.exceptions import GoogleCloudError
from mongoengine.errors import DoesNotExist, ValidationError
from dateutil import parser as date_parser

from ..db.models import Channel, ChannelType, Message, User
from ..services.utilities import require_group_membership, stringify_objectids
from ..services.message_handler import create_broadcast_message

messages = Blueprint("messages", __name__)


@messages.route("/group/<group_id>/channels/<channel_id>/messages", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_messages(group_id, channel_id):
    try:
        channel = Channel.objects.get(group=group_id, id=channel_id)
        if channel.type is not ChannelType.TEXT:
            return jsonify({"err": "Channel is not text channel"}), 400
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    limit = max(1, request.args.get("limit", 50, int))

    # 2) build your PyMongo query dict
    query = {"channel": ObjectId(channel_id)}
    if before_ts := request.args.get("before"):
        try:
            query["created_at"] = {"$lt": date_parser.isoparse(before_ts)}
        except Exception:
            return jsonify(err="Invalid before timestamp"), 400
    elif before_id := request.args.get("before_id"):
        try:
            query["_id"] = {"$lt": ObjectId(before_id)}
        except Exception:
            return jsonify(err="Invalid before_id"), 400

    # 3) raw cursor, sorted, limited, batched
    cursor = (
        Message.objects(__raw__=query).order_by("-created_at").limit(limit).as_pymongo()
    ).batch_size(10)

    docs = [stringify_objectids(doc) for doc in cursor]

    for doc in docs:
        doc["id"] = doc.pop("_id")

    resp = {"messages": docs}
    if len(docs) == limit:
        resp["next_cursor"] = docs[-1]["created_at"]
    return jsonify(resp), 200


@messages.route(
    "/group/<group_id>/channels/<channel_id>/messages/<message_id>", methods=["GET"]
)
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_message(group_id, channel_id, message_id):
    try:
        channel = Channel.objects.get(group=group_id, id=channel_id)
        if channel.type is not ChannelType.TEXT:
            return jsonify({"err": "Channel is not text channel"}), 400
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    try:
        message = Message.objects.get(channel=channel_id, id=message_id)
    except DoesNotExist:
        return jsonify({"err": "Message not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid message ID"}), 400

    return jsonify(message.to_dict()), 200


@messages.route("/group/<group_id>/channels/<channel_id>/messages", methods=["POST"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def create_message(group_id, channel_id):
    try:
        channel = Channel.objects.get(group=group_id, id=channel_id)
        if channel.type != ChannelType.TEXT:
            return jsonify({"err": "Channel is not text channel"}), 400
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    files = request.files.getlist("attachments")
    reply_to = request.files.get("reply_to")
    content = request.form.get("content", "").strip()
    if not content and not files:
        return jsonify({"err": "Missing message content"}), 400

    try:
        msg = create_broadcast_message(
            channel=channel,
            author=get_jwt_identity(),
            content=content,
            reply_to=reply_to,
            file_streams=files,
        )
    except GoogleCloudError:
        current_app.logger.exception("GCS upload failed")
        return jsonify({"err": "Failed to upload attachments"}), 503
    except Exception:
        current_app.logger.exception("Unexpected error in create_broadcast_message")
        return jsonify({"err": "Internal server error"}), 500

    return jsonify(msg.to_dict()), 201


@messages.route("/group/<group_id>/channels/<channel_id>/messages/gemini", methods=["POST"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def create_gemini_message(group_id, channel_id):
    try:
        channel = Channel.objects.get(group=group_id, id=channel_id)
        if channel.type != ChannelType.TEXT:
            return jsonify({"err": "Channel is not text channel"}), 400
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400
    
    try:
        gemini = User.objects.get(username="gemini")
    except DoesNotExist:
        return jsonify({"err": "Gemini not found"}), 404
    
    reply_to = request.files.get("reply_to")
    content = request.form.get("content", "").strip()

    try:
        msg = create_broadcast_message(
            channel=channel,
            author=gemini,
            content=content,
            reply_to=reply_to,
            file_streams=[]
        )
    except Exception as e:
        current_app.logger.exception("Unexpected error in create_broadcast_message: %s", e)
        return jsonify({"err": "Internal server error:"}), 500

    return jsonify(msg.to_dict()), 201