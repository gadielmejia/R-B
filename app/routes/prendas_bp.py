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
from app.models.inventario import Inventario
from app.models.lote import Lote
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
            item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None), 'idLote': getattr(inv, 'idLote', None)} for inv in p.inventarios]
            item['lotes'] = [{
                'idLote': lote.idLote,
                'nombre_lote': lote.nombre_lote,
                'descripcion_lote': lote.descripcion_lote,
                'cantidad_prendas': lote.cantidad_prendas
            } for lote in p.lotes]
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
        item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None), 'idLote': getattr(inv, 'idLote', None)} for inv in prenda.inventarios]
        item['lotes'] = [{
            'idLote': lote.idLote,
            'nombre_lote': lote.nombre_lote,
            'descripcion_lote': lote.descripcion_lote,
            'cantidad_prendas': lote.cantidad_prendas
        } for lote in prenda.lotes]
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
        results = []
        for p in prendas:
            item = serialize_model(p)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in p.imagenes]
            item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None)} for inv in p.inventarios]
            results.append(item)
        return response_success(results, "Prendas obtenidas exitosamente")
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

            inventory_codes = request.form.get('inventory_codes')
            inventory_items = []
            lote_data = request.form.get('lote_data')
            lote_model = None
            if lote_data:
                try:
                    import json
                    lote_payload = json.loads(lote_data)
                except Exception:
                    lote_payload = None
                if lote_payload and isinstance(lote_payload, dict):
                    lote_model = Lote(
                        idPrenda=prenda.idPrenda,
                        nombre_lote=lote_payload.get('nombre_lote', f"Lote de {nombre}"),
                        descripcion_lote=lote_payload.get('descripcion_lote'),
                        cantidad_prendas=0
                    )
                    db.session.add(lote_model)
                    db.session.flush()

            if inventory_codes:
                try:
                    import json
                    parsed_codes = json.loads(inventory_codes)
                except Exception:
                    parsed_codes = inventory_codes

                # parsed_codes can be a list of strings or a list of objects {codigo, talla} or {codigo_interno, talla}
                codes_list = []
                if isinstance(parsed_codes, str):
                    codes_list = [parsed_codes]
                elif isinstance(parsed_codes, list):
                    codes_list = parsed_codes
                else:
                    return response_error("El campo 'inventory_codes' debe ser una lista.", 400)

                # Normalize to list of tuples (code, talla)
                normalized = []
                for item in codes_list:
                    if isinstance(item, dict):
                        code = (item.get('codigo') or item.get('codigo_interno') or '').strip().upper()
                        talla_item = item.get('talla') if item.get('talla') is not None else None
                    else:
                        code = str(item).strip().upper()
                        talla_item = None
                    if code:
                        normalized.append((code, talla_item))

                codes = [c for c, t in normalized]
                codes = list(dict.fromkeys(codes))

                if codes:
                    existing = Inventario.query.filter(Inventario.codigo_interno.in_(codes)).all()
                    if existing:
                        duplicates = ", ".join([item.codigo_interno for item in existing])
                        return response_error(f"Los siguientes códigos ya existen: {duplicates}", 400)
                    # Create inventory items preserving talla when provided
                    for code, talla_item in normalized:
                        if code:
                            inv = Inventario(idPrenda=prenda.idPrenda, codigo_interno=code, estado='Disponible', talla=talla_item, idLote=lote_model.idLote if lote_model else None)
                            db.session.add(inv)
                            inventory_items.append(inv)
            if lote_model:
                lote_model.cantidad_prendas = len(inventory_items)

            db.session.commit()

            item = serialize_model(prenda)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in saved_images]
            item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None), 'idLote': getattr(inv, 'idLote', None)} for inv in inventory_items]
            item['lotes'] = [serialize_model(lote_model)] if lote_model else []
            item['lote'] = serialize_model(lote_model) if lote_model else None
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
        db.session.add(prenda)
        db.session.flush()

        inventory_items = []
        lote_model = None
        if 'lote_data' in data and data['lote_data']:
            lote_payload = data['lote_data']
            if isinstance(lote_payload, dict):
                lote_model = Lote(
                    idPrenda=prenda.idPrenda,
                    nombre_lote=lote_payload.get('nombre_lote', f"Lote de {data['nombre_prenda']}"),
                    descripcion_lote=lote_payload.get('descripcion_lote'),
                    nombre_prenda=lote_payload.get('nombre_prenda', data['nombre_prenda']),
                    descripcion_prenda=lote_payload.get('descripcion_prenda', data.get('descripcion')),
                    cantidad_prendas=0
                )
                db.session.add(lote_model)
                db.session.flush()

        if 'inventory_codes' in data and data['inventory_codes']:
            codes = data['inventory_codes']
            if not isinstance(codes, list):
                return response_error("El campo 'inventory_codes' debe ser una lista.", 400)

            normalized = []
            for item in codes:
                if isinstance(item, dict):
                    code = (item.get('codigo') or item.get('codigo_interno') or '').strip().upper()
                    talla_item = item.get('talla') if item.get('talla') is not None else None
                else:
                    code = str(item).strip().upper()
                    talla_item = None
                if code:
                    normalized.append((code, talla_item))

            codes_list = [c for c, t in normalized]
            codes_list = list(dict.fromkeys(codes_list))
            if codes_list:
                existing = Inventario.query.filter(Inventario.codigo_interno.in_(codes_list)).all()
                if existing:
                    duplicates = ", ".join([item.codigo_interno for item in existing])
                    return response_error(f"Los siguientes códigos ya existen: {duplicates}", 400)
                for code, talla_item in normalized:
                    inv = Inventario(idPrenda=prenda.idPrenda, codigo_interno=code, estado='Disponible', talla=talla_item, idLote=lote_model.idLote if lote_model else None)
                    db.session.add(inv)
                    inventory_items.append(inv)
        if lote_model:
            lote_model.cantidad_prendas = len(inventory_items)

        db.session.commit()
        item = serialize_model(prenda)
        item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None), 'idLote': getattr(inv, 'idLote', None)} for inv in inventory_items]
        item['lote'] = serialize_model(lote_model) if lote_model else None
        return response_success(item, "Prenda creada exitosamente", 201)
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

            # Manejo de lote único: actualizar o eliminar lote existente
            remove_lote = request.form.get('remove_lote')
            lote_data = request.form.get('lote_data')
            if remove_lote:
                for lote in list(prenda.lotes):
                    for inv in lote.inventarios:
                        inv.idLote = None
                    db.session.delete(lote)
            elif lote_data:
                try:
                    import json
                    lote_payload = json.loads(lote_data)
                except Exception:
                    lote_payload = None

                if lote_payload and isinstance(lote_payload, dict):
                    nombre_lote = lote_payload.get('nombre_lote')
                    if prenda.lotes:
                        lote_model = prenda.lotes[0]
                        lote_model.nombre_lote = nombre_lote or lote_model.nombre_lote
                        lote_model.descripcion_lote = lote_payload.get('descripcion_lote', lote_model.descripcion_lote)
                        # eliminar lotes extra si existieran
                        for extra in prenda.lotes[1:]:
                            for inv in extra.inventarios:
                                inv.idLote = None
                            db.session.delete(extra)
                    else:
                        lote_model = Lote(
                            idPrenda=prenda.idPrenda,
                            nombre_lote=nombre_lote or f"Lote de {prenda.nombre_prenda}",
                            descripcion_lote=lote_payload.get('descripcion_lote'),
                            cantidad_prendas=0
                        )
                        db.session.add(lote_model)
                        db.session.flush()
                        for inv in prenda.inventarios:
                            inv.idLote = lote_model.idLote

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

            # Eliminar códigos de inventario existentes marcados para remover
            remove_inventory_ids = request.form.get('remove_inventory_ids')
            removed_ids = []
            if remove_inventory_ids:
                try:
                    import json
                    removed_ids = json.loads(remove_inventory_ids)
                except Exception:
                    removed_ids = []
                for inv_id in removed_ids:
                    inv = Inventario.query.get(int(inv_id))
                    if inv and inv.idPrenda == prenda.idPrenda:
                        db.session.delete(inv)

            # Agregar nuevos códigos de inventario
            inventory_codes = request.form.get('inventory_codes')
            if inventory_codes:
                try:
                    parsed_codes = json.loads(inventory_codes)
                except Exception:
                    parsed_codes = inventory_codes
                if isinstance(parsed_codes, str):
                    codes = [parsed_codes]
                elif isinstance(parsed_codes, list):
                    codes = parsed_codes
                else:
                    return response_error("El campo 'inventory_codes' debe ser una lista.", 400)
                # normalized handling: accept list of strings or list of objects
                normalized = []
                for item in codes:
                    if isinstance(item, dict):
                        code = (item.get('codigo') or item.get('codigo_interno') or '').strip().upper()
                        talla_item = item.get('talla') if item.get('talla') is not None else None
                    else:
                        code = str(item).strip().upper()
                        talla_item = None
                    if not code:
                        continue
                    if Inventario.query.filter_by(codigo_interno=code).first():
                        return response_error(f"El código de inventario '{code}' ya existe.", 400)
                    # Solo agregar nuevos códigos si no existen en la prenda
                    inv = Inventario(idPrenda=prenda.idPrenda, codigo_interno=code, talla=talla_item)
                    db.session.add(inv)

            db.session.commit()
            remaining = PrendaImagen.query.filter_by(idPrenda=prenda.idPrenda).count()
            if remaining == 0:
                return response_error("La prenda debe tener al menos una imagen.", 400)

            prenda.save()
            item = serialize_model(prenda)
            item['images'] = [{'idImagen': img.idImagen, 'filename': img.filename, 'url': _image_url(img.filename)} for img in prenda.imagenes]
            item['inventory'] = [{'idInventario': inv.idInventario, 'codigo_interno': inv.codigo_interno, 'estado': inv.estado, 'talla': getattr(inv, 'talla', None), 'idLote': getattr(inv, 'idLote', None)} for inv in prenda.inventarios]
            item['lotes'] = [{
                'idLote': lote.idLote,
                'nombre_lote': lote.nombre_lote,
                'descripcion_lote': lote.descripcion_lote,
                'cantidad_prendas': lote.cantidad_prendas
            } for lote in prenda.lotes]
            item['lote'] = item['lotes'][0] if item['lotes'] else None
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
        # Eliminar inventario asociado antes de borrar la prenda para evitar errores de clave foránea.
        for inv in list(prenda.inventarios):
            db.session.delete(inv)
        prenda.delete()
        return response_success(message="Prenda eliminada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
