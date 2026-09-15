from flask import Blueprint, request
from app.models.lote import Lote
from app.models.prenda import Prenda
from app.utils.auth_middleware import token_required, employee_required
from app.utils.response import response_success, response_error, serialize_model

lotes_bp = Blueprint('lotes', __name__, url_prefix='/api/lotes')


@lotes_bp.route('', methods=['GET'])
@employee_required
def get_lotes():
    try:
        query = Lote.query
        id_prenda = request.args.get('idPrenda')

        if id_prenda is not None and id_prenda != '':
            query = query.filter_by(idPrenda=int(id_prenda))

        lotes = query.order_by(Lote.idLote.desc()).all()
        return response_success([serialize_model(lote) for lote in lotes], "Lotes obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)


@lotes_bp.route('/<int:id>', methods=['GET'])
@employee_required
def get_lote(id):
    try:
        lote = Lote.query.get(id)
        if not lote:
            return response_error("Lote no encontrado", 404)
        return response_success(serialize_model(lote), "Lote obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)


@lotes_bp.route('', methods=['POST'])
@token_required
def create_lote():
    try:
        data = request.get_json(silent=True) or {}

        if not data:
            return response_error("El body debe ser un JSON válido", 400)

        required_fields = ['idPrenda', 'nombre_lote']
        for field in required_fields:
            if field not in data or str(data[field]).strip() == '':
                return response_error(f"El campo '{field}' es requerido", 400)

        if not Prenda.query.get(data['idPrenda']):
            return response_error("La prenda especificada no existe", 404)

        lote = Lote(
            idPrenda=data['idPrenda'],
            nombre_lote=data['nombre_lote'],
            descripcion_lote=data.get('descripcion_lote'),
            cantidad_prendas=data.get('cantidad_prendas', 0),
        )
        lote.save()

        return response_success(serialize_model(lote), "Lote creado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)


@lotes_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_lote(id):
    try:
        lote = Lote.query.get(id)
        if not lote:
            return response_error("Lote no encontrado", 404)

        data = request.get_json(silent=True) or {}
        if not data:
            return response_error("El body debe ser un JSON válido", 400)

        if 'idPrenda' in data:
            if data['idPrenda'] is None or not Prenda.query.get(data['idPrenda']):
                return response_error("La prenda especificada no existe", 404)
            lote.idPrenda = data['idPrenda']

        if 'nombre_lote' in data:
            lote.nombre_lote = data['nombre_lote']
        if 'descripcion_lote' in data:
            lote.descripcion_lote = data['descripcion_lote']
        if 'cantidad_prendas' in data:
            lote.cantidad_prendas = data['cantidad_prendas']

        lote.save()
        return response_success(serialize_model(lote), "Lote actualizado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)


@lotes_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_lote(id):
    try:
        lote = Lote.query.get(id)
        if not lote:
            return response_error("Lote no encontrado", 404)

        lote.delete()
        return response_success(message="Lote eliminado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
