import uuid

from flask import Blueprint, current_app, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine.errors import DoesNotExist, ValidationError
from google.api_core.exceptions import NotFound
from werkzeug.utils import secure_filename
from bson import ObjectId

from .models import Group, GroupMembership, RoleType
from .utilities import delete_blob, generate_signed_url, require_group_membership, upload_to_gcs, validate_image_file

groups = Blueprint("groups", __name__)


@groups.route("/user-groups", methods=["GET"])
@jwt_required()
def get_groups():
    memberships = GroupMembership.objects(user=get_jwt_identity()).select_related()
    groups = []
    for membership in memberships:
        group = membership.group.fetch()
        data = group.to_mongo().to_dict()

        data["id"] = str(data.pop("_id"))
        data["created_at"] = data.pop("created_at").isoformat()

        try:
            img_url = generate_signed_url(
                blob_name = group.img_path,
                bucket_name = current_app.config["GCS_BUCKET_NAME"]
            )
        except Exception as e:
            current_app.logger.exception("Failed to get group image url: %s", e)
        data["img_url"] = img_url

        groups.append(data)

    return jsonify(groups), 200


@groups.route("/group/<group_id>", methods=["GET"])
@jwt_required()
@require_group_membership(group_arg="group_id")
def get_group(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group ID"}), 400
    
    try:
        img_url = generate_signed_url(
            blob_name = group.img_path,
            bucket_name = current_app.config["GCS_BUCKET_NAME"]
        )
    except Exception as e:
        current_app.logger.exception("Failed to get group image url: %s", e)

    return jsonify(
        {
            "id": str(group.id),
            "name": group.name,
            "description": group.description,
            "img_path": group.img_path,
            "img_url": img_url,
            "created_at": group.created_at.isoformat(),
        }
    ), 200


@groups.route("/group", methods=["POST"])
@jwt_required()
def create_group():
    name = request.form.get("name")
    if not name:
        return jsonify({"err": "Missing group name"}), 400
    if len(name) < 4:
        return jsonify({"err": "Name too short"}), 422

    description = request.form.get("description", "").strip()
    if len(description) > 150:
        return jsonify({"err": "Description too long"}), 422

    img_file = request.files.get("img")
    if not img_file:
        return jsonify({"err": "Missing image file"}), 400
    err = validate_image_file(img_file)
    if err:
        payload, code = err
        return jsonify(payload), code

    group_id = ObjectId()  # generate id early to append to img directory

    group = Group(id=group_id, name=name, description=description or None)

    original = secure_filename(img_file.filename)
    unique = f"groups/{group_id}/{uuid.uuid4().hex}_{original}"

    try:
        upload_to_gcs(
            file=img_file,
            bucket_name=current_app.config["GCS_BUCKET_NAME"],
            blob_name=unique,
        )
    except Exception as e:
        current_app.logger.exception("Failed to upload group image: %s", e)
        return jsonify({"err": "Image upload failed"}), 500

    group.img_path = unique

    # add creator as owner of group
    membership = GroupMembership(
        user=get_jwt_identity(), group=group, role=RoleType.OWNER
    )

    try:
        group.save()
        membership.save()
    except Exception as e:
        if group.pk:
            group.delete()
        current_app.logger.exception("Failed to save Group or Membership: %s", e)
        return jsonify({"err": "Could not create group"}), 500
    
    try:
        img_url = generate_signed_url(
            blob_name = group.img_path,
            bucket_name = current_app.config["GCS_BUCKET_NAME"]
        )
    except Exception as e:
        current_app.logger.exception("Failed to get group image url: %s", e)

    return (
        jsonify(
            {
                "id": str(group.id),
                "name": group.name,
                "description": group.description,
                "img_path": group.img_path,
                "img_url": img_url,
                "created_at": group.created_at.isoformat(),
            }
        ),
        201,
        {
            "Location": url_for(
                "groups.get_group", group_id=str(group.id), _external=True
            )
        },
    )


@groups.route("/group/<group_id>", methods=["PATCH"])
@jwt_required()
@require_group_membership(roles=[RoleType.OWNER], group_arg="group_id")
def update_group(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group id"}), 400

    name = request.form.get("name", "").strip()
    if name:
        if len(name) < 4:
            return jsonify({"err": "Name too short"}), 422
        group.name = name

    description = request.form.get("description", "").strip()
    if description:
        if len(description) > 150:
            return jsonify({"err": "Description too long"}), 422
        group.description = description

    img_file = request.files.get("img")
    if img_file:
        err = validate_image_file(img_file)
        if err:
            payload, code = err
            return jsonify(payload), code

        try:
            upload_to_gcs(
                file=img_file,
                bucket_name=current_app.config["GCS_BUCKET_NAME"],
                blob_name=group.img_path,
            )
        except Exception:
            current_app.logger.exception("Failed to upload new group image")
            return jsonify({"err": "Image upload failed"}), 502

    try:
        group.save()
    except Exception:
        current_app.logger.exception("Failed to update group")
        return jsonify(err="Could not update group"), 500
    
    try:
        img_url = generate_signed_url(
            blob_name = group.img_path,
            bucket_name = current_app.config["GCS_BUCKET_NAME"]
        )
    except Exception as e:
        current_app.logger.exception("Failed to get group image url: %s", e)

    return jsonify(
        {
            "id": str(group.id),
            "name": group.name,
            "description": group.description,
            "img_path": group.img_path,
            "img_url": img_url,
            "created_at": group.created_at.isoformat(),
        }
    ), 200


@groups.route("/group/<group_id>", methods=["DELETE"])
@jwt_required()
@require_group_membership(roles=[RoleType.OWNER], group_arg="group_id")
def delete_group(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except DoesNotExist:
        return jsonify({"err": "Group not found"}), 404
    except ValidationError:
        return jsonify({"err": "Invalid group id"}), 400

    try:
        group.delete()
    except Exception:
        current_app.logger.exception("Failed to delete group")
        return jsonify(err="Could not delete group"), 500

    try:
        delete_blob(
            bucket_name=current_app.config["GCS_BUCKET_NAME"],
            blob_name=group.img_path,
        )
        return "", 204
    except NotFound:
        current_app.logger.warning("Group image not found")
        return "", 204
    except Exception:
        current_app.logger.exception("Failed to delete image for %s", group_id)
        return "", 204
