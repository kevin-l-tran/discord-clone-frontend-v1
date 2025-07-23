from flask import jsonify, request


def require_json_fields(*fields):
    data = request.get_json(silent=True) or {}
    for field in fields:
        if not data.get(field):
            return jsonify(
                {"err": f"Missing {field}"}
            ), 400  # return tuple (Response, status_code)
    return data
