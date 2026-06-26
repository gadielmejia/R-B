from flask import Blueprint, request
from app.database.database import db
from app.models.comprobante import Comprobante
from app.models.reserva import Reserva
from app.utils.response import response_success, response_error, serialize_model, serialize_models
import uuid
from datetime import datetime

comprobantes_bp = Blueprint('comprobantes', __name__, url_prefix='/api/comprobantes')

@comprobantes_bp.route('', methods=['GET'])
def get_comprobantes():
    try:
        items = Comprobante.query.all()
        return response_success(serialize_models(items), "Comprobantes obtenidos")
    except Exception as e:
        return response_error(str(e), 500)

@comprobantes_bp.route('/reserva/<int:id_reserva>', methods=['GET'])
def get_comprobante_reserva(id_reserva):
    try:
        comp = Comprobante.query.filter_by(idReserva=id_reserva).first()
        if not comp:
            return response_error("Comprobante no encontrado", 404)
        return response_success(serialize_model(comp), "Comprobante obtenido")
    except Exception as e:
        return response_error(str(e), 500)

@comprobantes_bp.route('', methods=['POST'])
def create_comprobante():
    try:
        data = request.get_json()
        if not data:
            return response_error("Body inválido", 400)
        required = ['idReserva', 'monto_total']
        for f in required:
            if f not in data:
                return response_error(f"El campo '{f}' es requerido", 400)
        if not Reserva.query.get(data['idReserva']):
            return response_error("Reserva no encontrada", 404)
        numero = f"COMP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        comp = Comprobante(
            idReserva=data['idReserva'],
            numero_comprobante=numero,
            tipo_comprobante=data.get('tipo_comprobante', 'Ticket'),
            monto_total=data['monto_total'],
            estado='Emitido',
            descripcion=data.get('descripcion', '')
        )
        comp.save()
        return response_success(serialize_model(comp), "Comprobante generado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)
