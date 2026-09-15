from flask import Blueprint, request
from app.database.database import db
from app.models.reserva import Reserva
from app.models.usuarios import Usuarios
from app.models.inventario import Inventario
from app.models.detalle_reserva import Detalle_Reserva
from app.utils.auth_middleware import token_required
from app.utils.response import response_success, response_error, serialize_model, serialize_models

reservas_bp = Blueprint('reservas', __name__, url_prefix='/api/reservas')


def serialize_detalle_reserva(detalle):
    data = serialize_model(detalle)
    data['nombre_prenda'] = detalle.inventario.prenda.nombre_prenda if detalle.inventario and detalle.inventario.prenda else None
    data['codigo_interno'] = detalle.inventario.codigo_interno if detalle.inventario else None
    data['talla'] = detalle.inventario.talla if detalle.inventario else None
    return data


def serialize_reserva(reserva):
    data = serialize_model(reserva)
    data['nombre_cliente'] = reserva.cliente.nombre if reserva.cliente else None
    data['detalles_reserva'] = [serialize_detalle_reserva(detalle) for detalle in reserva.detalles_reserva]
    return data

                                  
@reservas_bp.route('', methods=['GET'])
def get_reservas():
    try:
        reservas = Reserva.query.all()
        return response_success([serialize_reserva(reserva) for reserva in reservas], "Reservas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                                                                      
@reservas_bp.route('/crear-con-detalles', methods=['POST'])
@token_required
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
        
                                   
        required_fields = ['id_cliente', 'id_administrador', 'fecha_reserva', 'fecha_evento', 
                          'fecha_inicio', 'fecha_fin', 'detalles']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        
                          
        detalles = data.get('detalles', [])
        if not isinstance(detalles, list) or len(detalles) == 0:
            return response_error("El campo 'detalles' debe ser una lista no vacía", 400)
        
                                            
        if not Usuarios.query.get(data['id_cliente']):
            return response_error("El cliente especificado no existe", 400)
        if not Usuarios.query.get(data['id_administrador']):
            return response_error("El administrador especificado no existe", 400)
        
                                                                         
        seen_inventarios = set()
        for detalle in detalles:
            id_inv = detalle.get('idInventario')
            cantidad = detalle.get('cantidad', 1)
            if not id_inv:
                return response_error("Cada detalle debe tener 'idInventario'", 400)
            if cantidad != 1:
                return response_error("Cada detalle debe representar una unidad de inventario individual con cantidad 1", 400)
            if id_inv in seen_inventarios:
                return response_error("No se pueden reservar dos veces el mismo inventario en una sola reserva", 400)
            seen_inventarios.add(id_inv)

            inv = db.session.query(Inventario).with_for_update().filter_by(idInventario=id_inv).first()
            if not inv:
                return response_error(f"Inventario {id_inv} no encontrado", 404)
            
            if inv.estado != 'Disponible':
                return response_error(f"El inventario {inv.codigo_interno} no está disponible (estado: {inv.estado})", 400)
        
                          
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
        
                                                              
        for detalle in detalles:
            id_inv = detalle.get('idInventario')
            subtotal = detalle.get('subtotal', 0)
            
                                      
            det_reserva = Detalle_Reserva(
                idReserva=reserva.idReserva,
                idInventario=id_inv,
                cantidad=1,
                subtotal=subtotal
            )
            det_reserva.save()
            
                                                 
            inv = db.session.query(Inventario).with_for_update().filter_by(idInventario=id_inv).first()
            inv.estado = 'Reservado'
            inv.save()
        
        return response_success(serialize_reserva(reserva), "Reserva creada exitosamente con inventarios actualizados", 201)
    except Exception as e:
        return response_error(str(e), 500)

                              
@reservas_bp.route('/<int:id>', methods=['GET'])
def get_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        return response_success(serialize_reserva(reserva), "Reserva obtenida exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                                    
@reservas_bp.route('/cliente/<int:id_cliente>', methods=['GET'])
def get_reservas_by_cliente(id_cliente):
    try:
        reservas = Reserva.query.filter_by(id_cliente=id_cliente).all()
        return response_success([serialize_reserva(reserva) for reserva in reservas], "Reservas obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                            
@reservas_bp.route('', methods=['POST'])
@token_required
def create_reserva():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
                                   
        required_fields = ['id_cliente', 'id_administrador', 'fecha_reserva', 'fecha_evento', 
                          'fecha_inicio', 'fecha_fin']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        
                                            
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
        
        return response_success(serialize_reserva(reserva), "Reserva creada exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

                          
@reservas_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
                                                   
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
                                                            

                    inv.save()
                except Exception:
                    failed_updates.append(det.idInventario)

            if failed_updates:
                msg = f"Reserva actualizada, pero fallaron al actualizar inventarios: {failed_updates}"
                return response_success(serialize_reserva(reserva), msg, 200)

        return response_success(serialize_reserva(reserva), "Reserva actualizada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                           
@reservas_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_reserva(id):
    try:
        reserva = Reserva.query.get(id)
        if not reserva:
            return response_error("Reserva no encontrada", 404)
        
        reserva.delete()
        
        return response_success(message="Reserva eliminada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
