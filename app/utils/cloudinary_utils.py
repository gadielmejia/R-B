import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from flask import current_app
import os
import uuid
from werkzeug.utils import secure_filename


def init_cloudinary(app):
    cloud_name = app.config.get('CLOUDINARY_CLOUD_NAME')
    api_key = app.config.get('CLOUDINARY_API_KEY')
    api_secret = app.config.get('CLOUDINARY_API_SECRET')
    cloudinary_url_value = app.config.get('CLOUDINARY_URL')

    # Priorizar credenciales explícitas si están todas presentes.
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        return

    if cloudinary_url_value:
        cloudinary.config(cloudinary_url=cloudinary_url_value, secure=True)
        return

    raise RuntimeError(
        'Cloudinary no está configurado. Agrega CLOUDINARY_URL o '
        'CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET en .env'
    )


def _cloudinary_public_id(filename):
    basename = secure_filename(filename)
    name, _ = os.path.splitext(basename)
    return f"{uuid.uuid4().hex}_{name}"


def upload_file_to_cloudinary(file_storage, folder=None):
    public_id = _cloudinary_public_id(file_storage.filename)
    upload_result = cloudinary.uploader.upload(
        file_storage,
        public_id=public_id,
        folder=folder or current_app.config.get('CLOUDINARY_UPLOAD_FOLDER'),
        overwrite=True,
        resource_type='image',
    )
    return upload_result.get('public_id')


def get_cloudinary_url(public_id):
    if not public_id:
        return ''
    url, _ = cloudinary_url(public_id, secure=True, resource_type='image')
    return url
