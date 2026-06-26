
from flask import Blueprint, request
from app.database.database import db
from app.models.cita import Cita
from app.models.usuarios import Usuarios
from app.utils.response import response_success, response_error, serialize_model, serialize_models

citas_bp = Blueprint('citas', __name__, url_prefix='/api/citas')

@citas_bp.route('', methods=['GET'])
def get_citas():
    try:
        citas = Cita.query.all()
        return response_success(serialize_models(citas), "Citas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

@citas_bp.route('/cliente/<int:id_cliente>', methods=['GET'])
def get_citas_cliente(id_cliente):
    try:
        citas = Cita.query.filter_by(id_cliente=id_cliente).all()
        return response_success(serialize_models(citas), "Citas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

@citas_bp.route('', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        if not data:
            return response_error("Body inválido", 400)
        required = ['id_cliente', 'id_administrador', 'fecha_cita']
        for f in required:
            if f not in data:
                return response_error(f"El campo '{f}' es requerido", 400)
        if not Usuarios.query.get(data['id_cliente']):
            return response_error("Cliente no encontrado", 404)
        if not Usuarios.query.get(data['id_administrador']):
            return response_error("Administrador no encontrado", 404)
        cita = Cita(
            id_cliente=data['id_cliente'],
            id_administrador=data['id_administrador'],
            id_reserva=data.get('id_reserva'),
            fecha_cita=data['fecha_cita'],
            motivo=data.get('motivo', ''),
            estado='Pendiente'
        )
        cita.save()
        return response_success(serialize_model(cita), "Cita agendada exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

@citas_bp.route('/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return response_error("Cita no encontrada", 404)
        data = request.get_json()
        if 'estado' in data:
            cita.estado = data['estado']
        if 'fecha_cita' in data:
            cita.fecha_cita = data['fecha_cita']
        if 'motivo' in data:
            cita.motivo = data['motivo']
        cita.save()
        return response_success(serialize_model(cita), "Cita actualizada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

@citas_bp.route('/<int:id>', methods=['DELETE'])
def delete_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return response_error("Cita no encontrada", 404)
        cita.delete()
        return response_success(message="Cita cancelada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

