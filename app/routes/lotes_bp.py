from flask import Blueprint, request

from app.database.database import db
from app.models.lote import Lote
from app.models.prenda import Prenda
from app.utils.response import response_success, response_error, serialize_model, serialize_models

lotes_bp = Blueprint('lotes', __name__, url_prefix='/api/lotes')


@lotes_bp.route('', methods=['GET'])
def get_lotes():
    try:
        id_prenda = request.args.get('idPrenda', type=int)
        query = Lote.query
        if id_prenda is not None:
            query = query.filter_by(idPrenda=id_prenda)
        lotes = query.order_by(Lote.idLote.desc()).all()
        return response_success(serialize_models(lotes), "Lotes obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)


@lotes_bp.route('', methods=['POST'])
def create_lote():
    try:
        data = request.get_json(silent=True) or {}

        if 'idPrenda' not in data:
            return response_error("El campo 'idPrenda' es requerido", 400)
        if 'nombre_lote' not in data:
            return response_error("El campo 'nombre_lote' es requerido", 400)

        prenda = Prenda.query.get(data['idPrenda'])
        if not prenda:
            return response_error("La prenda especificada no existe", 400)

        lote = Lote(
            idPrenda=data['idPrenda'],
            nombre_lote=data['nombre_lote'],
            descripcion_lote=data.get('descripcion_lote'),
            cantidad_prendas=data.get('cantidad_prendas', 0),
        )
        db.session.add(lote)
        db.session.commit()

        return response_success(serialize_model(lote), "Lote creado exitosamente", 201)
    except Exception as e:
        db.session.rollback()
        return response_error(str(e), 500)


@lotes_bp.route('/<int:id>', methods=['PUT'])
def update_lote(id):
    try:
        lote = Lote.query.get(id)
        if not lote:
            return response_error("Lote no encontrado", 404)

        data = request.get_json(silent=True) or {}

        if 'idPrenda' in data and data['idPrenda'] is not None:
            prenda = Prenda.query.get(data['idPrenda'])
            if not prenda:
                return response_error("La prenda especificada no existe", 400)
            lote.idPrenda = data['idPrenda']

        if 'nombre_lote' in data and data['nombre_lote'] is not None:
            lote.nombre_lote = data['nombre_lote']

        if 'descripcion_lote' in data:
            lote.descripcion_lote = data['descripcion_lote']

        if 'cantidad_prendas' in data and data['cantidad_prendas'] is not None:
            lote.cantidad_prendas = data['cantidad_prendas']

        db.session.commit()
        return response_success(serialize_model(lote), "Lote actualizado exitosamente")
    except Exception as e:
        db.session.rollback()
        return response_error(str(e), 500)


@lotes_bp.route('/<int:id>', methods=['DELETE'])
def delete_lote(id):
    try:
        lote = Lote.query.get(id)
        if not lote:
            return response_error("Lote no encontrado", 404)

        db.session.delete(lote)
        db.session.commit()
        return response_success(message="Lote eliminado exitosamente")
    except Exception as e:
        db.session.rollback()
        return response_error(str(e), 500)
