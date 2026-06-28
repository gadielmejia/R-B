from flask import Blueprint, request, current_app
import os
import uuid
from werkzeug.utils import secure_filename
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from app.database.database import db
from app.models.prenda import Prenda
from app.models.categoria import Categoria
from app.models.prenda_imagen import PrendaImagen
from app.utils.response import response_success, response_error, serialize_model, serialize_models

prendas_bp = Blueprint('prendas', __name__, url_prefix='/api/prendas')


def _cloudinary_public_id(filename):
    basename = secure_filename(filename)
    name, _ = os.path.splitext(basename)
    return f"{uuid.uuid4().hex}_{name}"


def _upload_to_cloudinary(file_storage):
    public_id = _cloudinary_public_id(file_storage.filename)
    upload_result = cloudinary.uploader.upload(
        file_storage,
        public_id=public_id,
        folder=current_app.config.get('CLOUDINARY_UPLOAD_FOLDER'),
        overwrite=True,
        resource_type='image',
    )
    return upload_result.get('public_id')


def _delete_from_cloudinary(public_id):
    try:
        if not public_id:
            return
        cloudinary.uploader.destroy(public_id, invalidate=True, resource_type='image')
    except Exception:
        pass


def _image_url(filename):
    if not filename:
        return ''
    if filename.startswith('http://') or filename.startswith('https://'):
        return filename

    try:
        # Always prefer Cloudinary for stored public IDs.
        url, _ = cloudinary_url(filename, secure=True, resource_type='image')
        return url
    except Exception:
        pass

    local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'prendas', filename)
    if os.path.exists(local_path):
        base = request.host_url.rstrip('/')
        return f"{base}/static/uploads/prendas/{filename}"

    return filename

# GET - Obtener todas las prendas
@prendas_bp.route('', methods=['GET'])
def get_prendas():
    try:
        prendas = Prenda.query.all()
        results = []
        for p in prendas:
            item = serialize_model(p)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in p.imagenes]
            results.append(item)
        return response_success(results, "Prendas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener prenda por ID
@prendas_bp.route('/<int:id>', methods=['GET'])
def get_prenda(id):
    try:
        prenda = Prenda.query.get(id)
        if not prenda:
            return response_error("Prenda no encontrada", 404)
        item = serialize_model(prenda)
        item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in prenda.imagenes]
        return response_success(item, "Prenda obtenida exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener prendas por categoría
@prendas_bp.route('/categoria/<int:id_categoria>', methods=['GET'])
def get_prendas_by_categoria(id_categoria):
    try:
        prendas = Prenda.query.filter_by(idCategoria=id_categoria).all()
        if not prendas:
            return response_error("No hay prendas en esta categoría", 404)
        return response_success(serialize_models(prendas), "Prendas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear nueva prenda
@prendas_bp.route('', methods=['POST'])
def create_prenda():
    try:
        # Soportar multipart/form-data con archivos en campo 'images' o JSON tradicional
        if request.content_type and 'multipart/form-data' in request.content_type:
            nombre = request.form.get('nombre_prenda')
            idCategoria = request.form.get('idCategoria')
            precio = request.form.get('precio_alquiler')
            descripcion = request.form.get('descripcion')
            talla = request.form.get('talla')
            color = request.form.get('color')

            # Validaciones
            if not nombre or not idCategoria or not precio:
                return response_error("Campos requeridos: nombre_prenda, idCategoria, precio_alquiler", 400)
            if not Categoria.query.get(int(idCategoria)):
                return response_error("La categoría especificada no existe", 400)

            files = request.files.getlist('images')
            if not files or len(files) == 0:
                return response_error("Debe subir al menos una imagen (máximo 10).", 400)
            if len(files) > 10:
                return response_error("Máximo 10 imágenes permitidas.", 400)

            prenda = Prenda(
                nombre_prenda=nombre,
                idCategoria=int(idCategoria),
                descripcion=descripcion,
                talla=talla,
                color=color,
                precio_alquiler=precio
            )
            db.session.add(prenda)
            db.session.flush()

            saved_images = []
            for f in files:
                if f and f.filename:
                    public_id = _upload_to_cloudinary(f)
                    img = PrendaImagen(idPrenda=prenda.idPrenda, filename=public_id)
                    db.session.add(img)
                    saved_images.append(img)
            db.session.commit()

            item = serialize_model(prenda)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in saved_images]
            return response_success(item, "Prenda creada exitosamente", 201)

        # Fallback JSON API
        data = request.get_json()
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        required_fields = ['nombre_prenda', 'idCategoria', 'precio_alquiler']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        if not Categoria.query.get(data['idCategoria']):
            return response_error("La categoría especificada no existe", 400)
        prenda = Prenda(
            nombre_prenda=data['nombre_prenda'],
            idCategoria=data['idCategoria'],
            descripcion=data.get('descripcion'),
            talla=data.get('talla'),
            color=data.get('color'),
            precio_alquiler=data['precio_alquiler']
        )
        prenda.save()
        return response_success(serialize_model(prenda), "Prenda creada exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar prenda
@prendas_bp.route('/<int:id>', methods=['PUT'])
def update_prenda(id):
    try:
        prenda = Prenda.query.get(id)
        if not prenda:
            return response_error("Prenda no encontrada", 404)
        # Soportar multipart para subir nuevas imágenes y eliminar existentes
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Campos del formulario
            nombre = request.form.get('nombre_prenda')
            if nombre is not None:
                prenda.nombre_prenda = nombre
            if 'idCategoria' in request.form:
                idCategoria = request.form.get('idCategoria')
                if not Categoria.query.get(int(idCategoria)):
                    return response_error("La categoría especificada no existe", 400)
                prenda.idCategoria = int(idCategoria)
            if 'precio_alquiler' in request.form:
                prenda.precio_alquiler = request.form.get('precio_alquiler')
            if 'descripcion' in request.form:
                prenda.descripcion = request.form.get('descripcion')
            if 'talla' in request.form:
                prenda.talla = request.form.get('talla')
            if 'color' in request.form:
                prenda.color = request.form.get('color')

            # Eliminar imágenes indicadas
            remove_ids = request.form.get('remove_image_ids')
            ids = []
            if remove_ids:
                try:
                    import json
                    ids = json.loads(remove_ids)
                except Exception:
                    ids = []
                for iid in ids:
                    img = PrendaImagen.query.get(int(iid))
                    if img and img.idPrenda == prenda.idPrenda:
                        _delete_from_cloudinary(img.filename)
                        db.session.delete(img)

            # Añadir nuevas imágenes
            new_files = request.files.getlist('images')
            total_images_now = len(prenda.imagenes) - len(ids)
            if new_files:
                if total_images_now + len(new_files) > 10:
                    return response_error("Máximo 10 imágenes permitidas.", 400)
                for f in new_files:
                    if f and f.filename:
                        public_id = _upload_to_cloudinary(f)
                        img = PrendaImagen(idPrenda=prenda.idPrenda, filename=public_id)
                        db.session.add(img)

            db.session.commit()
            remaining = PrendaImagen.query.filter_by(idPrenda=prenda.idPrenda).count()
            if remaining == 0:
                return response_error("La prenda debe tener al menos una imagen.", 400)

            prenda.save()
            item = serialize_model(prenda)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in prenda.imagenes]
            return response_success(item, "Prenda actualizada exitosamente")

        # Fallback JSON update
        data = request.get_json()
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        # Actualizar solo los campos proporcionados
        if 'nombre_prenda' in data:
            prenda.nombre_prenda = data['nombre_prenda']
        if 'descripcion' in data:
            prenda.descripcion = data['descripcion']
        if 'talla' in data:
            prenda.talla = data['talla']
        if 'color' in data:
            prenda.color = data['color']
        if 'precio_alquiler' in data:
            prenda.precio_alquiler = data['precio_alquiler']
        if 'idCategoria' in data:
            if not Categoria.query.get(data['idCategoria']):
                return response_error("La categoría especificada no existe", 400)
            prenda.idCategoria = data['idCategoria']

        prenda.save()
        return response_success(serialize_model(prenda), "Prenda actualizada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# DELETE - Eliminar prenda
@prendas_bp.route('/<int:id>', methods=['DELETE'])
def delete_prenda(id):
    try:
        prenda = Prenda.query.get(id)
        if not prenda:
            return response_error("Prenda no encontrada", 404)
        for img in prenda.imagenes:
            _delete_from_cloudinary(img.filename)
        prenda.delete()
        return response_success(message="Prenda eliminada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
