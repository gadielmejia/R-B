import json
from flask import Blueprint, request
from app.database.database import db
from app.models.inventario import Inventario
from app.models.prenda import Prenda
from app.models.lote import Lote
from app.utils.response import response_success, response_error, serialize_model, serialize_models
from app.routes.prendas_bp import _image_url

inventario_bp = Blueprint('inventario', __name__, url_prefix='/api/inventario')

# GET - Obtener todo el inventario
@inventario_bp.route('', methods=['GET'])
def get_inventario():
    try:
        items = Inventario.query.all()
        return response_success(serialize_models(items), "Inventario obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener item por ID
@inventario_bp.route('/<int:id>', methods=['GET'])
def get_item_inventario(id):
    try:
        item = Inventario.query.get(id)
        if not item:
            return response_error("Item no encontrado", 404)
        return response_success(serialize_model(item), "Item obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener items por estado
@inventario_bp.route('/estado/<estado>', methods=['GET'])
def get_items_by_estado(estado):
    try:
        items = Inventario.query.filter_by(estado=estado).all()
        if not items:
            return response_error(f"No hay items con estado '{estado}'", 404)

        results = []
        for inv in items:
            prenda = inv.prenda
            thumbnail = ''
            if prenda and getattr(prenda, 'imagenes', None):
                first_img = prenda.imagenes[0]
                thumbnail = _image_url(first_img.filename) if first_img else ''

            results.append({
                'idInventario': inv.idInventario,
                'codigo_interno': inv.codigo_interno,
                'talla': getattr(inv, 'talla', None),
                'estado': inv.estado,
                'idPrenda': getattr(inv, 'idPrenda', None),
                'prenda': {
                    'idPrenda': prenda.idPrenda if prenda else None,
                    'nombre_prenda': prenda.nombre_prenda if prenda else None,
                    'color': prenda.color if prenda else None,
                    'thumbnail_url': thumbnail
                }
            })

        return response_success(results, "Items obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)


# GET - Resumen de inventario (counts por estado)
@inventario_bp.route('/summary', methods=['GET'])
def get_inventario_summary():
    try:
        states = ['Disponible', 'Reservado', 'Alquilado', 'Reparacion']
        summary = {s: Inventario.query.filter_by(estado=s).count() for s in states}
        total = Inventario.query.count()
        return response_success({
            'total': total,
            'by_estado': summary
        }, "Resumen de inventario")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Agregar item al inventario
@inventario_bp.route('', methods=['POST'])
def create_item_inventario():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Validar campos requeridos
        if 'lote_data' in data and data['lote_data'] is not None:
            required_fields = ['idPrenda']
        else:
            required_fields = ['idPrenda', 'codigo_interno']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)

        # Verificar que la prenda existe
        if not Prenda.query.get(data['idPrenda']):
            return response_error("La prenda especificada no existe", 400)

        # Verificar que el código interno es único cuando no se crea un lote completo
        if ('lote_data' not in data or data['lote_data'] is None) and Inventario.query.filter_by(codigo_interno=data['codigo_interno']).first():
            return response_error("El código interno ya existe", 400)

        prenda = Prenda.query.get(data['idPrenda'])
        lote_model = None
        created_items = []
        lote_payload = data.get('lote_data')
        if lote_payload:
            if isinstance(lote_payload, str):
                try:
                    lote_payload = json.loads(lote_payload)
                except Exception:
                    lote_payload = None
            if not isinstance(lote_payload, dict):
                return response_error("El campo 'lote_data' debe ser un objeto JSON válido", 400)

            detalles = lote_payload.get('detalles_prenda')
            if isinstance(detalles, str):
                try:
                    detalles = json.loads(detalles)
                except Exception:
                    detalles = None

            if not isinstance(detalles, list) or len(detalles) == 0:
                return response_error("El campo 'detalles_prenda' debe ser una lista de objetos con 'codigo_interno'", 400)

            normalized = []
            for detalle in detalles:
                if not isinstance(detalle, dict):
                    return response_error("Cada detalle de prenda debe ser un objeto", 400)
                codigo = (detalle.get('codigo_interno') or detalle.get('codigo') or '').strip().upper()
                if not codigo:
                    continue
                talla_item = detalle.get('talla')
                normalized.append({'codigo_interno': codigo, 'talla': talla_item})

            if len(normalized) == 0:
                return response_error("No se encontraron códigos válidos en 'detalles_prenda'", 400)

            unique_codes = [item['codigo_interno'] for item in normalized]
            if len(unique_codes) != len(set(unique_codes)):
                return response_error("Hay códigos duplicados en 'detalles_prenda'", 400)

            existing = Inventario.query.filter(Inventario.codigo_interno.in_(unique_codes)).all()
            if existing:
                duplicates = ", ".join([item.codigo_interno for item in existing])
                return response_error(f"Los siguientes códigos ya existen: {duplicates}", 400)

            lote_model = Lote(
                idPrenda=data['idPrenda'],
                nombre_lote=lote_payload.get('nombre_lote', f"Lote de {prenda.nombre_prenda}"),
                descripcion_lote=lote_payload.get('descripcion_lote'),
                cantidad_prendas=lote_payload.get('cantidad_prendas', len(normalized))
            )
            db.session.add(lote_model)
            db.session.flush()

            for detalle in normalized:
                inv = Inventario(
                    idPrenda=data['idPrenda'],
                    codigo_interno=detalle['codigo_interno'],
                    estado=data.get('estado', 'Disponible'),
                    talla=detalle['talla'],
                    idLote=lote_model.idLote
                )
                db.session.add(inv)
                created_items.append(inv)

            db.session.commit()
            lote_data_response = serialize_model(lote_model)
            lote_data_response['detalles_prenda'] = normalized
            return response_success({
                'lote': lote_data_response,
                'inventory': [serialize_model(inv) for inv in created_items]
            }, "Lote e inventario creados exitosamente", 201)

        if Inventario.query.filter_by(codigo_interno=data['codigo_interno']).first():
            return response_error("El código interno ya existe", 400)

        item = Inventario(
            idPrenda=data['idPrenda'],
            codigo_interno=data['codigo_interno'],
            estado=data.get('estado', 'Disponible'),
            talla=data.get('talla'),
            idLote=None
        )
        item.save()

        return response_success(serialize_model(item), "Item agregado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar estado del inventario
@inventario_bp.route('/<int:id>', methods=['PUT'])
def update_item_inventario(id):
    try:
        item = Inventario.query.get(id)
        if not item:
            return response_error("Item no encontrado", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        if 'estado' in data:
            valid_states = ['Disponible', 'Reservado', 'Alquilado', 'Reparacion']
            if data['estado'] not in valid_states:
                return response_error(f"Estado inválido. Estados válidos: {', '.join(valid_states)}", 400)
            item.estado = data['estado']
        
        item.save()
        
        return response_success(serialize_model(item), "Item actualizado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# DELETE - Eliminar item del inventario
@inventario_bp.route('/<int:id>', methods=['DELETE'])
def delete_item_inventario(id):
    try:
        item = Inventario.query.get(id)
        if not item:
            return response_error("Item no encontrado", 404)
        
        item.delete()
        
        return response_success(message="Item eliminado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
