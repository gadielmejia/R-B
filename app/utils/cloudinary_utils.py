import cloudinary


def init_cloudinary(app):
    cloud_name = app.config.get('CLOUDINARY_CLOUD_NAME')
    api_key = app.config.get('CLOUDINARY_API_KEY')
    api_secret = app.config.get('CLOUDINARY_API_SECRET')
    cloudinary_url = app.config.get('CLOUDINARY_URL')

    # Priorizar credenciales explícitas si están todas presentes.
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        return

    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
        return

    raise RuntimeError(
        'Cloudinary no está configurado. Agrega CLOUDINARY_URL o ' 
        'CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET en .env'
    )
