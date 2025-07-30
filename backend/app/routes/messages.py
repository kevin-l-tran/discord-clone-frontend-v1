from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from google.cloud.exceptions import GoogleCloudError
from mongoengine.errors import DoesNotExist, ValidationError
from dateutil import parser as date_parser

from ..db.models import Channel, ChannelType, Message
from ..services.utilities import require_group_membership
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

    limit = request.args.get("limit", default=50, type=int)
    if limit < 1:
        return jsonify({"err": "Limit must be at least 1"}), 400

    before_ts = request.args.get("before", type=str)
    before_id = request.args.get("before_id", type=str)

    raw = Message.objects(channel=channel_id)

    if before_ts:
        try:
            cut_off = date_parser.isoparse(before_ts)
        except (ValueError, TypeError):
            return jsonify({"err": "Invalid before timestamp"}), 400
        raw = raw.filter(created_at__lt=cut_off)
    elif before_id:
        try:
            oid = ObjectId(before_id)
        except Exception:
            return jsonify({"err": "Invalid before_id"}), 400
        raw = raw.filter(id__lt=oid)

    raw = raw.order_by("-created_at", "-id").limit(limit)
    messages = [msg.to_dict() for msg in raw]

    next_cursor = None
    if len(messages) == limit:
        last = messages[-1]
        next_cursor = last["created_at"].isoformat()

    resp = {"messages": messages}
    if next_cursor:
        resp["next_cursor"] = next_cursor

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
            channel = channel,
            author = get_jwt_identity(),
            content = content,
            reply_to = reply_to,
            file_streams = files
        )
    except GoogleCloudError:
        current_app.logger.exception("GCS upload failed")
        return jsonify({"err": "Failed to upload attachments"}), 503
    except Exception:
        current_app.logger.exception("Unexpected error in create_broadcast_message")
        return jsonify({"err": "Internal server error"}), 500

    return jsonify(msg.to_json()), 201
