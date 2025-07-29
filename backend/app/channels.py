from flask import Blueprint, current_app, jsonify, request, url_for
from flask_jwt_extended import jwt_required
from mongoengine.errors import DoesNotExist, ValidationError

from .models import ChannelType, Group, Channel, RoleType
from .utilities import require_group_membership, require_json_fields

channels = Blueprint("channels", __name__)


@channels.route("/group/<group_id>/channels", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_channels(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    channels = []

    raw = Channel.objects(group=group)
    for channel in raw:
        channels.append(channel.to_dict())

    return jsonify(channels), 200


@channels.route("/group/<group_id>/channels/<channel_id>", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_channel(group_id, channel_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        channel = Channel.objects.get(group=group, id=channel_id)
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    return jsonify(channel.to_dict()), 200


@channels.route("/group/<group_id>/channels", methods=["PATCH"])
@jwt_required()
@require_group_membership(group_arg="group_id", roles=[RoleType.OWNER])
@require_json_fields("name", "type", "topic")
def create_channel(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    channel = Channel(group=group)

    data = request.json_data
    name = data["name"].strip()
    ctype = data["type"].strip()
    topic = data["topic"].strip()

    if not name:
        return jsonify({"err": "Channel name empty"}), 400
    if Channel.objects(group=group, name__iexact=name):
        return jsonify({"err": "Channel name already exists"}), 409
    channel.name = name

    try:
        channel.type = ChannelType(ctype)
    except ValueError:
        return jsonify({"err": "Invalid channel type"}), 400

    channel.topic = topic

    try:
        channel.save()
        return (
            jsonify(channel.to_dict()),
            201,
            {
                "Location": url_for(
                    "channels.get_channel",
                    group_id=str(group.id),
                    channel_id=str(channel.id),
                    _external=True,
                )
            },
        )
    except Exception as e:
        current_app.logger.exception("Failed to save Channel: %s", e)
        return jsonify({"err": "Could not save Channel"}), 500


# you cannot change the type of channel
# changing from text to voice would require mass message deletion
@channels.route("/group/<group_id>/channels/<channel_id>", methods=["PATCH"])
@jwt_required()
@require_group_membership(group_arg="group_id", roles=[RoleType.OWNER])
def update_channel(group_id, channel_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        channel = Channel.objects.get(group=group, id=channel_id)
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify(err="Request body must be JSON"), 400

    name = data.get("name").strip()
    if name is not None:
        if not isinstance(name, str):
            return jsonify({"err": "name must be a string"}), 400
        if not name:
            return jsonify({"err": "Channel name empty"}), 400
        if Channel.objects(group=group, name__iexact=name):
            return jsonify({"err": "Channel name already exists"}), 409
        channel.name = name

    topic = data.get("topic").strip()
    if topic is not None:
        if not isinstance(topic, str):
            return jsonify({"err": "topic must be a string"}), 400
        channel.topic = topic

    position = data.get("position")
    if position is not None:
        if not isinstance(position, int):
            return jsonify({"err": "position must be an integer"}), 400
        channel.position = position

    try:
        channel.save()
        return jsonify(channel.to_dict()), 200
    except Exception as e:
        current_app.logger.exception("Failed to save Channel: %s", e)
        return jsonify({"err": "Could not save Channel"}), 500


@channels.route("/group/<group_id>/channels/<channel_id>", methods=["DELETE"])
@jwt_required()
@require_group_membership(group_arg="group_id", roles=[RoleType.OWNER])
def delete_channel(group_id, channel_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        channel = Channel.objects.get(group=group, id=channel_id)
    except DoesNotExist:
        return jsonify({"err": "Channel not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid channel ID"}), 400

    try:
        channel.delete()
        return "", 204
    except Exception as e:
        current_app.logger.exception("Failed to delete Channel: %s", e)
        return jsonify({"err": "Could not delete Channel"}), 500
