from typing import Iterable, Optional
import uuid

from google.cloud.exceptions import GoogleCloudError
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app

from .utilities import delete_blob, upload_to_gcs
from ..db.models import Channel, Message, User
from .. import socketio


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def emit_chat(payload, channel):
    socketio.emit("chat:recv", payload, room=channel)


def create_broadcast_message(
    channel: Channel,
    author: User,
    content: str,
    reply_to: Optional[Message],
    file_streams: Iterable[FileStorage],
):
    """
    Create and broadcast a new chat message with optional file attachments.

    This function performs the following steps:
    1) Uploads each provided file stream to GCS, generating
       a temporary signed URL for each upload.
    2) Persists the message record to the database, including attachment filenames.
    3) Builds a JSON payload with database fields and the signed URLs.
    4) Broadcasts the payload over WebSocket to all clients subscribed to the channel.

    Args:
        channel: The channel where the message will be posted.
        author: The user who authored the message.
        content: The textual content of the message.
        file_streams: An iterable of file-like objects
            to be uploaded as attachments (e.g., Flask FileStorage instances).

    Returns:
        The newly created Message object as persisted in the database.
        Emits a 'chat:recv' event via Flask-SocketIO to notify clients on success.
        Logs errors to the Flask application logger on upload failure.

    Raises:
        GoogleCloudError: If any file upload to GCS fails, the exception is
            propagated and no message is persisted or broadcast.
    """
    # 1) Save files to GCS
    bucket_name = current_app.config["GCS_BUCKET_NAME"]
    attachment_names = []
    attachment_urls = []

    file_streams = file_streams or []
    for fs in file_streams:
        # secure the filename and namespace it with a UUID
        orig_name = secure_filename(fs.filename)
        unique_name = f"{uuid.uuid4().hex}_{orig_name}"
        blob_path = (
            f"groups/{str(channel.group.id)}/{str(channel.id)}/uploads/{unique_name}"
        )

        try:
            # upload_to_gcs returns a temporary signed URL
            url = upload_to_gcs(fs, bucket_name, blob_path)
            attachment_names.append(blob_path)
            attachment_urls.append(url)
        except GoogleCloudError as e:
            # if any upload fails, you might choose to abort the whole op
            # or skip this file; here we abort with an exception
            current_app.logger.error(f"GCS upload failed: {e}")
            raise

    # 2) Persist the Message
    msg = Message(
        channel=channel, author=author, content=content, attachments=attachment_names
    )
    if reply_to is not None:
        msg.reply_to = reply_to

    try:
        msg.save()
    except Exception as e:
        current_app.logger.error("Failed to save message: %s", e)
        for name in attachment_names:
            delete_blob(
                bucket_name=current_app.config["GCS_BUCKET_NAME"],
                blob_name=name,
            )
        raise

    # 3) Build a payload that includes both the DB fields and the temp URLs
    payload = msg.to_json()
    payload["attachment_urls"] = attachment_urls

    # 4) Broadcast the enriched payload
    try:
        emit_chat(payload, channel=str(channel.id))
    except RetryError as e:
        current_app.logger.error(f"All retries failed: {e}")

    return msg
