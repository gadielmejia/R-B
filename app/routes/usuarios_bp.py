from flask import Blueprint, request, current_app
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from app.database.database import db
from app.models.usuarios import Usuarios
from app.models.roles import Roles
from app.models.cita import Cita
from app.models.reserva import Reserva
from app.models.detalle_reserva import Detalle_Reserva
from app.models.comprobante import Comprobante
from app.utils.auth_middleware import token_required, employee_required
from app.utils.response import response_success, response_error, serialize_model, serialize_models
from app.utils.cloudinary_utils import upload_file_to_cloudinary, get_cloudinary_url
import hashlib
import jwt

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')


def is_sha256_hash(value):
    if not isinstance(value, str):
        return False
    value = value.lower()
    return len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def hash_password(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_password(value):
    if not isinstance(value, str) or not value:
        return value
    if is_sha256_hash(value):
        return value
    return generate_password_hash(value, method='scrypt')


def parse_user_payload():
    if request.content_type and 'multipart/form-data' in request.content_type:
        return request.form.to_dict()
    return request.get_json() or {}


def get_token_payload():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except Exception:
        return None


def is_admin_request():
    payload = get_token_payload()
    return payload and payload.get('rol') == 'admin'


def serialize_usuario(usuario):
    data = serialize_model(usuario, exclude_fields=['Contrasena'])
    data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None
    if usuario.avatar_url and not usuario.avatar_url.startswith('http'):
        data['avatar_url'] = get_cloudinary_url(usuario.avatar_url)
    return data


def eliminar_relaciones_usuario(id_usuario):
    reservas = Reserva.query.filter(
        (Reserva.id_cliente == id_usuario) | (Reserva.id_administrador == id_usuario)
    ).all()
    ids_reservas = [reserva.idReserva for reserva in reservas]

    if ids_reservas:
        db.session.query(Comprobante).filter(Comprobante.idReserva.in_(ids_reservas)).delete(synchronize_session=False)
        db.session.query(Detalle_Reserva).filter(Detalle_Reserva.idReserva.in_(ids_reservas)).delete(synchronize_session=False)
        db.session.query(Cita).filter(Cita.id_reserva.in_(ids_reservas)).delete(synchronize_session=False)

    db.session.query(Cita).filter(
        (Cita.id_cliente == id_usuario) | (Cita.id_administrador == id_usuario)
    ).delete(synchronize_session=False)

    if ids_reservas:
        db.session.query(Reserva).filter(
            (Reserva.id_cliente == id_usuario) | (Reserva.id_administrador == id_usuario)
        ).delete(synchronize_session=False)


@usuarios_bp.route('', methods=['GET'])
@employee_required
def get_usuarios():
    try:
        usuarios = Usuarios.query.all()
        return response_success([serialize_usuario(usuario) for usuario in usuarios], "Usuarios obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                              
@usuarios_bp.route('/<int:id>', methods=['GET'])
@employee_required
def get_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)
        return response_success(serialize_usuario(usuario), "Usuario obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                            
@usuarios_bp.route('', methods=['POST'])
def create_usuario():
    try:
        data = parse_user_payload()

        if not data:
            return response_error("El body debe ser un JSON válido o multipart/form-data", 400)

        required_fields = ['nombre', 'documento', 'correo', 'Contrasena']
        for field in required_fields:
            if field not in data or str(data[field]).strip() == "":
                return response_error(f"El campo '{field}' es requerido", 400)

        if Usuarios.query.filter_by(documento=data['documento']).first():
            return response_error("El documento ya está registrado", 400)
        correo_lower = data['correo'].strip().lower()
        if Usuarios.query.filter_by(correo=correo_lower).first():
            return response_error("El correo ya está registrado", 400)

        password = data['Contrasena']
        if is_sha256_hash(password):
            return response_error("La contraseña debe ser texto plano, no el hash", 400)

        if is_admin_request():
            id_rol = None
            if 'idRol' in data and data['idRol']:
                try:
                    id_rol = int(data['idRol'])
                except (TypeError, ValueError):
                    return response_error("El rol especificado no es válido", 400)
                if not Roles.query.get(id_rol):
                    return response_error("El rol especificado no existe", 400)
            if id_rol is None:
                cliente_role = Roles.query.filter(func.lower(Roles.nombre) == 'cliente').first()
                if not cliente_role:
                    return response_error("No se encontró el rol cliente en el sistema", 500)
                id_rol = cliente_role.idRol
        else:
            cliente_role = Roles.query.filter(func.lower(Roles.nombre) == 'cliente').first()
            if not cliente_role:
                return response_error("No se encontró el rol cliente en el sistema", 500)
            id_rol = cliente_role.idRol

        avatar_url = None
        if 'avatar' in request.files:
            try:
                avatar_url = upload_file_to_cloudinary(request.files['avatar'], folder=current_app.config.get('CLOUDINARY_UPLOAD_FOLDER'))
            except Exception as e:
                return response_error(f"Error al subir avatar: {str(e)}", 500)

        usuario = Usuarios(
            nombre=data['nombre'],
            documento=data['documento'],
            correo=correo_lower,
            Contrasena=generate_password_hash(password),
            idRol=id_rol,
            telefono=data.get('telefono'),
            avatar_url=avatar_url,
        )
        usuario.save()

        return response_success(serialize_usuario(usuario), "Usuario creado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

                          
@usuarios_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)

        data = parse_user_payload()

        if not data:
            return response_error("El body debe ser un JSON válido o multipart/form-data", 400)

        if 'nombre' in data:
            usuario.nombre = data['nombre']
        if 'documento' in data:
            existing = Usuarios.query.filter_by(documento=data['documento']).first()
            if existing and existing.idUsuario != id:
                return response_error("El documento ya está registrado", 400)
            usuario.documento = data['documento']
        if 'correo' in data:
            correo_lower = data['correo'].strip().lower()
            existing = Usuarios.query.filter_by(correo=correo_lower).first()
            if existing and existing.idUsuario != id:
                return response_error("El correo ya está registrado", 400)
            usuario.correo = correo_lower
        if 'telefono' in data:
            usuario.telefono = data['telefono'] or None
        if 'Contrasena' in data and data['Contrasena']:
            usuario.Contrasena = generate_password_hash(data['Contrasena'])
        if 'idRol' in data:
            if request.current_user.get('rol') != 'admin':
                return response_error("Solo un administrador puede cambiar roles", 403)
            try:
                id_rol = int(data['idRol'])
            except (TypeError, ValueError):
                return response_error("El rol especificado no es válido", 400)
            if not Roles.query.get(id_rol):
                return response_error("El rol especificado no existe", 400)
            usuario.idRol = id_rol

        if 'avatar' in request.files:
            try:
                usuario.avatar_url = upload_file_to_cloudinary(request.files['avatar'], folder=current_app.config.get('CLOUDINARY_UPLOAD_FOLDER'))
            except Exception as e:
                return response_error(f"Error al subir avatar: {str(e)}", 500)

        usuario.save()

        return response_success(serialize_usuario(usuario), "Usuario actualizado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                           
@usuarios_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)

        eliminar_relaciones_usuario(id)
        db.session.delete(usuario)
        db.session.commit()

        return response_success(message="Usuario eliminado exitosamente")
    except Exception as e:
        db.session.rollback()
        return response_error(str(e), 500)
