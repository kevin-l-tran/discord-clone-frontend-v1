import requests

from flask import Response, current_app, jsonify, request
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from werkzeug.datastructures import FileStorage
from google.cloud import storage
from functools import wraps


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
F = TypeVar('F', bound=Callable[..., Any])

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


def upload_to_gcs(
    file: FileStorage,
    bucket_name: str,
    blob_name: str
) -> str:
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
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_file(
        file,
        content_type=file.content_type
    )

    blob.make_public()
    return blob.public_url