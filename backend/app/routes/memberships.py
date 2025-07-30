from flask import Blueprint, current_app, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from ..services.utilities import require_group_membership
from ..db.models import Group, GroupMembership, RoleType, User

memberships = Blueprint("memberships", __name__)


@memberships.route("/group/<group_id>/members/<member_id>", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_member(group_id, member_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(id=member_id, group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    payload = {
        "membership": member.to_dict(),
        "user": member.user.to_dict(),
    }

    return jsonify(payload), 200


@memberships.route("/group/<group_id>/members/self", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def your_membership(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(user=get_jwt_identity(), group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    payload = {
        "membership": member.to_dict(),
        "user": member.user.to_dict(),
    }

    return jsonify(payload), 200


@memberships.route("/group/<group_id>/members", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_members(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    members = []

    raw = GroupMembership.objects(group=group).select_related()
    for member in raw:
        members.append({"membership": member.to_dict(), "user": member.user.to_dict()})

    return jsonify(members), 200


@memberships.route("/group/<group_id>/join", methods=["POST"])
@jwt_required()
def create_member(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    current_membership = GroupMembership.objects(
        user=get_jwt_identity(), group=group
    ).first()
    if current_membership:
        return jsonify({"err": "Already a member"}), 409

    membership = GroupMembership(
        user=get_jwt_identity(),
        group=group,
        role=RoleType.MEMBER,
    )

    try:
        membership.save()
        return (
            jsonify(membership.to_dict()),
            201,
            {
                "Location": url_for(
                    "memberships.get_member",
                    group_id=str(group.id),
                    member_id=str(membership.id),
                    _external=True,
                )
            },
        )
    except NotUniqueError:
        # Two requests tried to insert the same (user,group) at once
        return jsonify({"err": "Already a member"}), 409
    except Exception as e:
        current_app.logger.exception("Failed to save Membership: %s", e)
        return jsonify({"err": "Could not create Membership"}), 500


@memberships.route("/group/<group_id>/members/<member_id>", methods=["PATCH"])
@jwt_required()
@require_group_membership(roles=[RoleType.ADMIN, RoleType.OWNER], group_arg="group_id")
def update_member(group_id, member_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(id=member_id, group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    if member.role is RoleType.OWNER:
        return jsonify({"err": "Forbidden"}), 403

    current_member = GroupMembership.objects.get(user=get_jwt_identity(), group=group)
    if current_member.role is RoleType.ADMIN and member.role is RoleType.ADMIN:
        return jsonify({"err": "Forbidden"}), 403

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify(err="Request body must be JSON"), 400

    nickname = data.get("nickname")
    if nickname is not None:
        if not isinstance(nickname, str):
            return jsonify({"err": "nickname must be a string"}), 400
        member.nickname = nickname.strip()

    role = data.get("role")
    if role is not None:
        try:
            member.role = RoleType(role)
        except ValueError:
            return jsonify({"err": "Invalid role type"}), 400

    is_muted = data.get("is_muted")
    if is_muted is not None:
        if not isinstance(is_muted, bool):
            return jsonify({"err": "is_muted must be a boolean"}), 400
        member.is_muted = is_muted

    is_banned = data.get("is_banned")
    if is_banned is not None:
        if not isinstance(is_banned, bool):
            return jsonify({"err": "is_banned must be a boolean"}), 400
        member.is_banned = is_banned

    try:
        member.save()
        return jsonify(member.to_dict()), 200
    except Exception as e:
        current_app.logger.exception("Failed to save Membership: %s", e)
        return jsonify({"err": "Could not save Membership"}), 500


@memberships.route("/group/<group_id>/username", methods=["PATCH"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def update_username(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(user=get_jwt_identity(), group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify(err="Request body must be JSON"), 400

    nickname = data.get("nickname")
    if nickname is not None:
        if not isinstance(nickname, str):
            return jsonify({"err": "nickname must be a string"}), 400
        member.nickname = nickname.strip()

    try:
        member.save()
        return jsonify(member.to_dict()), 200
    except Exception as e:
        current_app.logger.exception("Failed to save nickname: %s", e)
        return jsonify({"err": "Could not save nickname"}), 500


@memberships.route("/group/<group_id>/members/<member_id>", methods=["DELETE"])
@jwt_required()
@require_group_membership(roles=[RoleType.OWNER], group_arg="group_id")
def delete_member(group_id, member_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(id=member_id, group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    if member.role is RoleType.OWNER:
        return jsonify({"err": "Forbidden"}), 403

    current_member = GroupMembership.objects.get(user=get_jwt_identity(), group=group)
    if current_member.role is RoleType.ADMIN and member.role is RoleType.ADMIN:
        return jsonify({"err": "Forbidden"}), 403

    try:
        member.delete()
        return "", 204
    except Exception as e:
        current_app.logger.exception("Failed to delete Membership: %s", e)
        return jsonify({"err": "Could not delete Membership"}), 500


@memberships.route("/group/<group_id>/members/", methods=["DELETE"])
@jwt_required()
@require_group_membership(roles=[RoleType.OWNER], group_arg="group_id")
def delete_self_member(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400

    try:
        member = GroupMembership.objects.get(id=get_jwt_identity(), group=group)
    except DoesNotExist:
        return jsonify({"err": "Membership not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid membership ID"}), 400

    try:
        member.delete()
        return "", 204
    except Exception as e:
        current_app.logger.exception("Failed to delete Membership: %s", e)
        return jsonify({"err": "Could not delete Membership"}), 500
