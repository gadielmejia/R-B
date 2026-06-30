from flask import Blueprint, request
from app.database.database import db
from app.models.reserva import Reserva
from app.models.usuarios import Usuarios
from app.models.inventario import Inventario
from app.models.detalle_reserva import Detalle_Reserva
from app.utils.response import response_success, response_error, serialize_model, serialize_models

reservas_bp = Blueprint('reservas', __name__, url_prefix='/api/reservas')

# GET - Obtener todas las reservas
@reservas_bp.route('', methods=['GET'])
def get_reservas():
    try:
        reservas = Reserva.query.all()
        return response_success(serialize_models(reservas), "Reservas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear reserva con detalles e inventarios (ANTES de /<int:id>)
@reservas_bp.route('/crear-con-detalles', methods=['POST'])
def create_reserva_con_detalles():
    """
    Crea una reserva, agrega los detalles de reserva y actualiza el estado del inventario.
    Body esperado:
    {
        "id_cliente": int,
        "id_administrador": int,
        "fecha_reserva": "YYYY-MM-DD",
        "fecha_evento": "YYYY-MM-DD",
        "fecha_inicio": "YYYY-MM-DD",
        "fecha_fin": "YYYY-MM-DD",
        "detalles": [
            { "idInventario": int, "cantidad": int, "subtotal": float }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Validar campos requeridos
        required_fields = ['id_cliente', 'id_administrador', 'fecha_reserva', 'fecha_evento', 
                          'fecha_inicio', 'fecha_fin', 'detalles']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        
        # Validar detalles
        detalles = data.get('detalles', [])
        if not isinstance(detalles, list) or len(detalles) == 0:
            return response_error("El campo 'detalles' debe ser una lista no vacía", 400)
        
        # Verificar que los usuarios existen
        if not Usuarios.query.get(data['id_cliente']):
            return response_error("El cliente especificado no existe", 400)
        if not Usuarios.query.get(data['id_administrador']):
            return response_error("El administrador especificado no existe", 400)
        
        # Verificar que todos los inventarios existen y están disponibles
        for detalle in detalles:
            id_inv = detalle.get('idInventario')
            if not id_inv:
                return response_error("Cada detalle debe tener 'idInventario'", 400)
            
            inv = Inventario.query.get(id_inv)
            if not inv:
                return response_error(f"Inventario {id_inv} no encontrado", 404)
            
            if inv.estado != 'Disponible':
                return response_error(f"El inventario {inv.codigo_interno} no está disponible (estado: {inv.estado})", 400)
        
        # Crear la reserva
        reserva = Reserva(
            id_cliente=data['id_cliente'],
            id_administrador=data['id_administrador'],
            fecha_reserva=data['fecha_reserva'],
            fecha_evento=data['fecha_evento'],
            fecha_inicio=data['fecha_inicio'],
            fecha_fin=data['fecha_fin'],
            fecha_devolucion=data.get('fecha_devolucion'),
            observaciones=data.get('observaciones'),
            estado='Pendiente'
        )
        reserva.save()
        
        # Agregar detalles de reserva y actualizar inventarios
        for detalle in detalles:
            id_inv = detalle.get('idInventario')
            cantidad = detalle.get('cantidad', 1)
            subtotal = detalle.get('subtotal', 0)
            
            # Crear detalle de reserva
            det_reserva = Detalle_Reserva(
                idReserva=reserva.idReserva,
                idInventario=id_inv,
                cantidad=cantidad,
                subtotal=subtotal
            )
            det_reserva.save()
            
            # Actualizar inventario a "Reservado"
            inv = Inventario.query.get(id_inv)
            inv.estado = 'Reservado'
            inv.save()
        
        return response_success(serialize_model(reserva), "Reserva creada exitosamente con inventarios actualizados", 201)
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener reserva por ID
@reservas_bp.route('/<int:id>', methods=['GET'])
def get_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        return response_success(serialize_model(reserva), "Reserva obtenida exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener reservas por cliente
@reservas_bp.route('/cliente/<int:id_cliente>', methods=['GET'])
def get_reservas_by_cliente(id_cliente):
    try:
        reservas = Reserva.query.filter_by(id_cliente=id_cliente).all()
        if not reservas:
            return response_error("No hay reservas para este cliente", 404)
        return response_success(serialize_models(reservas), "Reservas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear nueva reserva
@reservas_bp.route('', methods=['POST'])
def create_reserva():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Validar campos requeridos
        required_fields = ['id_cliente', 'id_administrador', 'fecha_reserva', 'fecha_evento', 
                          'fecha_inicio', 'fecha_fin']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        
        # Verificar que los usuarios existen
        if not Usuarios.query.get(data['id_cliente']):
            return response_error("El cliente especificado no existe", 400)
        if not Usuarios.query.get(data['id_administrador']):
            return response_error("El administrador especificado no existe", 400)
        
        reserva = Reserva(
            id_cliente=data['id_cliente'],
            id_administrador=data['id_administrador'],
            fecha_reserva=data['fecha_reserva'],
            fecha_evento=data['fecha_evento'],
            fecha_inicio=data['fecha_inicio'],
            fecha_fin=data['fecha_fin'],
            fecha_devolucion=data.get('fecha_devolucion'),
            observaciones=data.get('observaciones'),
            estado=data.get('estado', 'Pendiente')
        )
        reserva.save()
        
        return response_success(serialize_model(reserva), "Reserva creada exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar reserva
@reservas_bp.route('/<int:id>', methods=['PUT'])
def update_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Actualizar solo los campos proporcionados
        if 'estado' in data:
            reserva.estado = data['estado']
        if 'fecha_devolucion' in data:
            reserva.fecha_devolucion = data['fecha_devolucion']
        if 'observaciones' in data:
            reserva.observaciones = data['observaciones']
        if 'fecha_evento' in data:
            reserva.fecha_evento = data['fecha_evento']
        if 'fecha_inicio' in data:
            reserva.fecha_inicio = data['fecha_inicio']
        if 'fecha_fin' in data:
            reserva.fecha_fin = data['fecha_fin']
        
        reserva.save()

        # Si la reserva cambia de estado, actualizar inventarios según el nuevo estado
        if 'estado' in data:
            nuevo_estado = data['estado']
            detalles = Detalle_Reserva.query.filter_by(idReserva=reserva.idReserva).all()
            failed_updates = []
            for det in detalles:
                try:
                    inv = Inventario.query.get(det.idInventario)
                    if not inv:
                        failed_updates.append(det.idInventario)
                        continue

                    if nuevo_estado == 'Confirmada':
                        inv.estado = 'Alquilado'
                    elif nuevo_estado in ('Cancelada', 'Finalizada'):
                        inv.estado = 'Disponible'
                    # otros estados no cambian el inventario

                    inv.save()
                except Exception:
                    failed_updates.append(det.idInventario)

            if failed_updates:
                msg = f"Reserva actualizada, pero fallaron al actualizar inventarios: {failed_updates}"
                return response_success(serialize_model(reserva), msg, 200)

        return response_success(serialize_model(reserva), "Reserva actualizada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# DELETE - Eliminar reserva
@reservas_bp.route('/<int:id>', methods=['DELETE'])
def delete_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        
        reserva.delete()
        
        return response_success(message="Reserva eliminada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
