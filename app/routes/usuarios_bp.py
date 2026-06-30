from flask import Blueprint, request, current_app
from app.database.database import db
from app.models.usuarios import Usuarios
from app.models.roles import Roles
from app.utils.response import response_success, response_error, serialize_model, serialize_models
from werkzeug.security import generate_password_hash
from app.utils.cloudinary_utils import upload_file_to_cloudinary, get_cloudinary_url
import hashlib

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


def serialize_usuario(usuario):
    data = serialize_model(usuario)
    data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None
    if usuario.avatar_url and not usuario.avatar_url.startswith('http'):
        data['avatar_url'] = get_cloudinary_url(usuario.avatar_url)
    return data


# GET - Obtener todos los usuarios
@usuarios_bp.route('', methods=['GET'])
def get_usuarios():
    try:
        usuarios = Usuarios.query.all()
        return response_success([serialize_usuario(usuario) for usuario in usuarios], "Usuarios obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener usuario por ID
@usuarios_bp.route('/<int:id>', methods=['GET'])
def get_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)
        return response_success(serialize_usuario(usuario), "Usuario obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear nuevo usuario
@usuarios_bp.route('', methods=['POST'])
def create_usuario():
    try:
        data = parse_user_payload()

        if not data:
            return response_error("El body debe ser un JSON válido o multipart/form-data", 400)

        required_fields = ['nombre', 'documento', 'correo', 'Contrasena', 'idRol']
        for field in required_fields:
            if field not in data or str(data[field]).strip() == "":
                return response_error(f"El campo '{field}' es requerido", 400)

        if Usuarios.query.filter_by(documento=data['documento']).first():
            return response_error("El documento ya está registrado", 400)
        if Usuarios.query.filter_by(correo=data['correo']).first():
            return response_error("El correo ya está registrado", 400)

        data['Contrasena'] = normalize_password(data['Contrasena'])

        if 'idRol' not in data or not data['idRol']:
            return response_error("El rol es obligatorio al crear un usuario", 400)

        try:
            id_rol = int(data['idRol'])
        except (TypeError, ValueError):
            return response_error("El rol especificado no es válido", 400)

        if not Roles.query.get(id_rol):
            return response_error("El rol especificado no existe", 400)

        avatar_url = None
        if 'avatar' in request.files:
            try:
                avatar_url = upload_file_to_cloudinary(request.files['avatar'], folder=current_app.config.get('CLOUDINARY_UPLOAD_FOLDER'))
            except Exception as e:
                return response_error(f"Error al subir avatar: {str(e)}", 500)

        usuario = Usuarios(
            nombre=data['nombre'],
            documento=data['documento'],
            correo=data['correo'],
            Contrasena=data['Contrasena'],
            idRol=id_rol,
            telefono=data.get('telefono'),
            avatar_url=avatar_url,
        )
        usuario.save()

        return response_success(serialize_usuario(usuario), "Usuario creado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar usuario
@usuarios_bp.route('/<int:id>', methods=['PUT'])
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
            existing = Usuarios.query.filter_by(correo=data['correo']).first()
            if existing and existing.idUsuario != id:
                return response_error("El correo ya está registrado", 400)
            usuario.correo = data['correo']
        if 'telefono' in data:
            usuario.telefono = data['telefono'] or None
        if 'Contrasena' in data and data['Contrasena']:
            usuario.Contrasena = normalize_password(data['Contrasena'])
        if 'idRol' in data:
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

# DELETE - Eliminar usuario
@usuarios_bp.route('/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)

        usuario.delete()

        return response_success(message="Usuario eliminado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
