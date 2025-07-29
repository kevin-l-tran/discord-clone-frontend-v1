import requests
import datetime

from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple, TypeVar, Union
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from mongoengine.errors import DoesNotExist, ValidationError
from flask import Response, current_app, jsonify, request
from werkzeug.datastructures import FileStorage
from google.oauth2 import service_account
from google.cloud import storage
from datetime import timedelta
from functools import wraps
from PIL import Image

from .models import Group, GroupMembership, RoleType


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
    Performs an HTTP GET request to the specified URL and returns the parsed JSON response.

    Args:
        url: The endpoint URL to send the GET request to.
        params: Query parameters to include in the request.
        headers: HTTP headers to include in the request.
        timeout: Timeout duration in seconds for the HTTP request (default: 5).

    Returns:
        The parsed JSON response, which can be a dictionary or a list.

    Raises:
        ApiError: If the HTTP request fails (network error, non-2xx status) or if the response
                  cannot be parsed as JSON. The exception contains the HTTP status code if available.
    """
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.exception("API GET %s failed: %s", url, e)
        code = getattr(e.response, "status_code", None)
        raise ApiError(f"GET {url} failed: {e}", status_code=code)

    try:
        return resp.json()
    except ValueError as e:
        current_app.logger.exception("Invalid JSON from %s: %s", url, e)
        raise ApiError(f"Invalid JSON in response from {url}")


# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


def require_json_fields(*fields: str) -> Callable[[F], F]:
    """
    Decorator that ensures specified form fields are present and non-empty in the request.

    Args:
        *fields: One or more field names to validate in `request.form`.

    Returns:
        A decorator that wraps a Flask view function, enforcing that all
        specified fields are present and contain non-whitespace characters. If validation fails,
        returns a JSON error response with a 400 status.
    """

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Union[Response, Any]:
            data = request.get_json(silent=True) or {}
            for field in fields:
                value = data.get(field, "")
                if not isinstance(value, str) or not value.strip():
                    return jsonify({"err": f"Missing {field}"}), 400
            request.json_data = data
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def upload_to_gcs(file: FileStorage, bucket_name: str, blob_name: str) -> str:
    """
    Uploads a file to Google Cloud Storage and makes it publicly accessible.

    Args:
        file:
            The file object to upload. Typically this comes from Flask's
            `request.files`, e.g. `file = request.files['file']`.
        bucket_name:
            The name of the GCS bucket where the file will be stored.
        blob_name:
            The desired path and filename inside the bucket (e.g. "uploads/img.png").

    Returns:
        The publicly accessible URL of the uploaded file, e.g.
        "https://storage.googleapis.com/{bucket_name}/{destination_blob_name}".

    Raises:
        google.cloud.exceptions.GoogleCloudError:
            If any error occurs during interaction with GCS (authentication,
            permissions, network issues, etc.).
    """
    key_path = current_app.config.get("G_SECRETS_FILE")
    creds = service_account.Credentials.from_service_account_file(key_path)
    storage_client = storage.Client(credentials=creds, project=creds.project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_file(file, content_type=file.content_type)

    url = blob.generate_signed_url(
        version="v4", expiration=timedelta(minutes=15), method="GET"
    )
    return url


def generate_signed_url(
    blob_name: str, bucket_name: str, expires_in_seconds: int = 900
) -> str:
    """
    Generate a V4 signed URL for downloading a blob from Google Cloud Storage.
    This URL is valid for a limited time and uses the HTTP GET method.

    Args:
        blob_name:
            The path to the object within the bucket (e.g.
            "groups/1234/avatar.jpg").
        bucket_name:
            The name of the GCS bucket containing the object.
        expires_in_seconds:
            How many seconds from now the URL should remain valid.
            Defaults to 900 (15 minutes).

    Returns:
        A signed URL string that clients can use to download the object.

    Raises:
        google.api_core.exceptions.GoogleAPIError:
            If there’s a problem communicating with GCS or signing the URL.
    """
    key_path = current_app.config.get("G_SECRETS_FILE")
    creds = service_account.Credentials.from_service_account_file(key_path)
    storage_client = storage.Client(credentials=creds, project=creds.project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        expiration=datetime.timedelta(seconds=expires_in_seconds),
        version="v4",
        method="GET",
    )


def delete_blob(bucket_name: str, blob_name: str) -> None:
    """
    Delete an object (blob) from a Google Cloud Storage bucket.

    Args:
        bucket_name:
            The name of the Cloud Storage bucket containing the blob.
        blob_name:
            The path/key of the blob within the bucket (e.g.
            "groups/68861a9e0cb23ac215f2f137/avatar.jpg").

    Raises:
        google.api_core.exceptions.NotFound:
            If the specified blob does not exist in the bucket.
        google.api_core.exceptions.GoogleAPIError:
            For other GCS errors (permissions, network issues, etc.).
    """
    key_path = current_app.config.get("G_SECRETS_FILE")
    creds = service_account.Credentials.from_service_account_file(key_path)
    storage_client = storage.Client(credentials=creds, project=creds.project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


def validate_image_file(
    img_file: FileStorage, max_bytes: Optional[int] = None
) -> Optional[Tuple[dict, int]]:
    """
    Validates that an uploaded file is a real image within size limits.

    Checks, in order:
      1. MIME type starts with "image/".
      2. File size ≤ `max_bytes`.
      3. Full structure check via Pillow's `Image.verify()`.

    Args:
        img_file: The uploaded file from `request.files`.
        max_bytes: Maximum allowed size in bytes (default 5 MB).

    Returns:
        None if all checks pass, or a tuple `(payload, status_code)` where
        `payload` is a JSON-serializable dict `{"err": "..."}`
        and `status_code` is the HTTP code to return.
    """
    if not img_file.mimetype.startswith("image/"):
        return {"err": "File is not an image"}, 400

    DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
    if max_bytes is None:
        max_bytes = current_app.config.get("MAX_UPLOAD_BYTES", DEFAULT_MAX_BYTES)

    stream = img_file.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    if size > max_bytes:
        return {"err": "Image too large"}, 413

    try:
        img = Image.open(stream)
        img.verify()
        fmt = getattr(img, "format", None)
        if fmt is None:
            raise ValueError("Unknown format")
        stream.seek(0)
    except Exception:
        return {"err": "Corrupted or unsupported image"}, 400

    return None


def require_group_membership(
    roles: Optional[Iterable[RoleType]] = None,
    group_arg: str = "group_id",
):
    """
    Ensure that the JWT-authenticated user is a member of a given Group,
    and optionally has one of the specified roles, before allowing access
    to a Flask view.

    Args:
        roles:
            If provided, restricts access to only those users whose membership
            role is in this set. Must be an iterable of RoleType.
            If None, any member (regardless of role) is allowed.
        group_arg:
            The name of the keyword argument in the view function that provides
            the Group's ID. This ID will be used to look up the Group and the
            current user's membership.

    Returns:
        Out: The decorated Flask view's normal return value, or one of:
        - `(json, 500)` if `group_arg` missing
        - `(json, 404)` if group ID is invalid or not found
        - `(json, 403)` if the user has no membership or insufficient role
    """
    # validate the roles argument at decorate-time
    if roles is not None and not isinstance(roles, (list, tuple, set)):
        raise ValueError(
            "require_group_membership: 'roles' must be a list/tuple/set of RoleType"
        )
    # safely normalize into a set (or leave None)
    allowed_roles: Optional[Set[RoleType]] = set(roles) if roles is not None else None

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            if group_arg not in kwargs:
                return jsonify(
                    {"err": f"Decorator expected '{group_arg}' in kwargs"}
                ), 500
            group_id = kwargs[group_arg]

            try:
                group = Group.objects.get(id=group_id)
            except (DoesNotExist, ValidationError):
                return jsonify({"err": "Group not found"}), 404

            try:
                membership = GroupMembership.objects.get(user=user_id, group=group)
            except (DoesNotExist, ValidationError):
                return jsonify({"err": "Forbidden"}), 403

            if allowed_roles is not None and membership.role not in allowed_roles:
                return jsonify({"err": "Forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
