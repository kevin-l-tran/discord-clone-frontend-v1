from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import (
    create_access_token,
    current_user,
    get_jwt_identity,
    jwt_required,
)
from bson import ObjectId

from . import jwt
from .models import User
from .utilities import require_json_fields, api_get

auth = Blueprint("auth", __name__)


@auth.route("/signin", methods=["POST"])
@require_json_fields("username", "password")
def signin():
    data = request.json_data
    username = data["username"].strip()
    password = data["password"].strip()

    user = User.objects(username__iexact=username).first()

    if not user:
        return jsonify({"err": "Bad username"}), 401
    if not user.check_password(password):
        return jsonify({"err": "Bad password"}), 401

    access_token = create_access_token(identity=user)
    return jsonify({"access_token": access_token}), 200


@auth.route("/signup", methods=["POST"])
@require_json_fields("email", "username", "password")
def signup():
    data = request.json_data
    username = data["username"].strip()
    email = data["email"].strip()
    password = data["password"].strip()

    if len(username) < 4:
        return jsonify({"err": "Username too short"}), 422
    if len(password) < 8:
        return jsonify({"err": "Password too short"}), 422

    if User.objects(username__iexact=username).first():
        return jsonify({"err": "Username taken"}), 409
    if User.objects(email__iexact=email).first():
        return jsonify({"err": "Email taken"}), 409

    # email validate api
    url = "https://api.api-ninjas.com/v1/validateemail"
    params = {"email": email}
    headers = {"X-Api-Key": current_app.config["NINJA_API_KEY"]}
    response = api_get(url=url, params=params, headers=headers)
    if not response.get("is_valid"):
        return jsonify({"err": "Invalid email"}), 422
    if response.get("is_disposable"):
        return jsonify({"err": "Disposable email"}), 422

    # profanity check api
    url = "https://api.api-ninjas.com/v1/profanityfilter"
    params = {"text": username}
    headers = {"X-Api-Key": current_app.config["NINJA_API_KEY"]}
    response = api_get(url=url, params=params, headers=headers)
    if response.get("has_profanity"):
        return jsonify({"err": "Username has profanity"}), 422

    user = User()
    user.username = username
    user.email = email
    user.set_password(password)
    try:
        user.save(force_insert=True)
    except Exception as e:
        current_app.logger.exception("Failed to save User: %s", e)
        return jsonify({"err": "Could not create user"}), 500

    access_token = create_access_token(identity=user)
    return (
        jsonify({"access_token": access_token}),
        201,
        {"Location": url_for("auth.currentuser", _external=True)},
    )


@auth.route("/currentuser", methods=["GET"])
@jwt_required()
def currentuser():
    return jsonify(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
    )


@auth.route("/check/email-taken", methods=["GET"])
def check_email_taken():
    email = request.args.get("email")

    if User.objects(email__iexact=email).first():
        return jsonify({"err": "Email taken"}), 409

    return jsonify({"msg": "Good email"}), 200


@auth.route("/check/username-taken", methods=["GET"])
def check_username_taken():
    username = request.args.get("username")

    if User.objects(username__iexact=username).first():
        return jsonify({"err": "Username taken"}), 409

    return jsonify({"msg": "Good username"}), 200


@auth.route("/check/valid-email", methods=["GET"])
def check_valid_email():
    url = "https://api.api-ninjas.com/v1/validateemail"
    params = {"email": request.args.get("email")}
    headers = {"X-Api-Key": current_app.config["NINJA_API_KEY"]}
    response = api_get(url=url, params=params, headers=headers)

    if not response.get("is_valid"):
        return jsonify({"err": "Invalid email"}), 422
    if response.get("is_disposable"):
        return jsonify({"err": "Disposable email"}), 422

    return jsonify({"msg": "Good email"}), 200


@auth.route("/check/profanity", methods=["GET"])
def check_profanity():
    url = "https://api.api-ninjas.com/v1/profanityfilter"
    params = {"text": request.args.get("text")}
    headers = {"X-Api-Key": current_app.config["NINJA_API_KEY"]}
    response = api_get(url=url, params=params, headers=headers)

    if response.get("has_profanity"):
        return jsonify({"err": "Text has profanity"}), 422

    return jsonify({"msg": "No profanity"}), 200


@auth.route("/verify-token", methods=["GET"])
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    return jsonify({"msg": "Token is valid", "user": current_user}), 200


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.objects(id=ObjectId(identity)).first()


@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)


@jwt.additional_claims_loader
def add_claims_to_access_token(user):
    return {
        "username": user.username
    }
