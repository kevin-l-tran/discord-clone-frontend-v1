from flask import Blueprint, request, jsonify
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned
from flask_jwt_extended import create_access_token

from models import User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if not email:
        return jsonify({"msg": "Missing email"}), 400
    if not password:
        return jsonify({"msg": "Missing password"}), 400
    
    try:
        user = User.objects.get(email__iexact=email)
    except DoesNotExist:
        return jsonify({"msg": "Bad email"}), 401
    except MultipleObjectsReturned:
        return jsonify({"msg": "DB integrity broken (identical emails)"}), 500
    else:
        if not user.check_password(password):
            return jsonify({"msg": "Bad password"}), 401
        
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token), 200