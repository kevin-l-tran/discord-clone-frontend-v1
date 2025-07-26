import requests

from flask import Response, current_app, jsonify, request
from typing import Any, Dict, Optional, Tuple, Union


class ApiError(Exception):
    """Wraps errors from external API calls."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def api_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 5,
) -> Union[Dict[str, Any], list]:
    """
    Send a GET request to `url`, raising ApiError on failure.

    - `params`: query‐string parameters.
    - `headers`: any extra headers (e.g. auth tokens); merged with default API key header.
    - `timeout`: seconds before giving up.

    Returns the parsed JSON body (dict or list).
    """
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.error("API GET %s failed: %s", url, e)
        code = getattr(e.response, "status_code", None)
        raise ApiError(f"GET {url} failed: {e}", status_code=code)

    try:
        return resp.json()
    except ValueError as e:
        current_app.logger.error("Invalid JSON from %s: %s", url, e)
        raise ApiError(f"Invalid JSON in response from {url}")


def require_json_fields(*fields: str) -> Union[Dict[str, Any], Tuple[Response, int]]:
    """
    Validate that the incoming request JSON contains all specified keys.

    - `*fields`: One or more field names that must be present in the JSON payload.

    Returns a dict of the parsed JSON data if all required fields are present. 
    Otherwise returns a (Response, status_code) error tuple if any field is missing, 
    where Response is {"err": "Missing <field>"} and status_code is 400.
    """
    data = request.get_json(silent=True) or {}
    for field in fields:
        if not data.get(field):
            return jsonify(
                {"err": f"Missing {field}"}
            ), 400
    return data
