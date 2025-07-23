import requests

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import create_access_token, current_user, jwt_required
from bson import ObjectId

from . import jwt
from .models import User
from .utilities import require_json_fields

auth = Blueprint("auth", __name__)


@auth.route("/signin", methods=["POST"])
def signin():
    data = require_json_fields("username", "password")
    if isinstance(data, tuple):
        return data

    username = data["username"]
    password = data["password"]

    user = User.objects(username__iexact=username).first()

    if not user:
        return jsonify({"err": "Bad username"}), 401
    if not user.check_password(password):
        return jsonify({"err": "Bad password"}), 401

    access_token = create_access_token(identity=user)
    return jsonify({"access_token": access_token}), 200


@auth.route("/signup", methods=["POST"])
def signup():
    data = require_json_fields("username", "email", "password")
    if isinstance(data, tuple):
        return data

    username = data["username"]
    email = data["email"]
    password = data["password"]

    if User.objects(username__iexact=username).first():
        return jsonify({"err": "Username taken"}), 409
    if User.objects(email__iexact=email).first():
        return jsonify({"err": "Email taken"}), 409

    # email validate api
    api_url = "https://api.api-ninjas.com/v1/validateemail?email={}".format(email)
    try:
        response = requests.get(
            api_url, headers={"X-Api-Key": current_app.config["NINJA_API_KEY"]}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"err": "Update failed", "details": str(e)}), 502
    else:
        if not response.json()["is_valid"]:
            return jsonify({"err": "Invalid email"}), 422
        if response.json()["is_disposable"]:
            return jsonify({"err": "Disposable email"}), 422

    # profanity check api
    api_url = "https://api.api-ninjas.com/v1/profanityfilter?text={}".format(username)
    try:
        response = requests.get(
            api_url, headers={"X-Api-Key": current_app.config["NINJA_API_KEY"]}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"err": "Update failed", "details": str(e)}), 502
    else:
        if response.json()["has_profanity"]:
            return jsonify({"err": "Username has profanity"}), 422

    if len(username) < 4:
        return jsonify({"err": "Username too short"}), 422
    if len(password) < 8:
        return jsonify({"err": "Password too short"}), 422

    user = User()
    user.username = username
    user.email = email
    user.set_password(password)
    user.save(force_insert=True)

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
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )


@auth.route("/check/email", methods=["GET"])
def check_email():
    email = request.args.get("email")
    api_url = "https://api.api-ninjas.com/v1/validateemail?email={}".format(email)
    try:
        response = requests.get(
            api_url, headers={"X-Api-Key": current_app.config["NINJA_API_KEY"]}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"err": "Update failed", "details": str(e)}), 502
    else:
        if not response.json()["is_valid"]:
            return jsonify({"err": "Invalid email"}), 422
        if response.json()["is_disposable"]:
            return jsonify({"err": "Disposable email"}), 422

        return jsonify({"msg": "Good email"}), 200


@auth.route("/check/profanity", methods=["GET"])
def check_profanity():
    text = request.args.get("text")
    api_url = "https://api.api-ninjas.com/v1/profanityfilter?text={}".format(text)
    try:
        response = requests.get(
            api_url, headers={"X-Api-Key": current_app.config["NINJA_API_KEY"]}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"err": "Update failed", "details": str(e)}), 502
    else:
        if response.json()["has_profanity"]:
            return jsonify({"err": "Username has profanity"}), 422


@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.objects(id=ObjectId(identity)).first()
