from flask import Blueprint, request, current_app
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.usuarios import Usuarios
from app.utils.response import response_success, response_error, serialize_model
import jwt
import hashlib
import string
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def is_hex_string(value, length=64):
    if not isinstance(value, str) or len(value) != length:
        return False
    return all(c in string.hexdigits for c in value)


def sha256_hex(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_role_name(role_name):
    if not isinstance(role_name, str):
        return 'user'

    role_name = role_name.strip().lower()
    if role_name in ['admin', 'administrador']:
        return 'admin'
    if role_name == 'empleado':
        return 'empleado'
    return 'user'


def generate_token(usuario):
    payload = {
        'idUsuario': usuario.idUsuario,
        'correo': usuario.correo,
        'rol': normalize_role_name(usuario.rol.nombre if usuario.rol else None),
        'exp': datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'correo' not in data or 'Contrasena' not in data:
            return response_error("Correo y contraseña son requeridos", 400)

        correo = data['correo'].strip().lower()
        usuario = Usuarios.query.filter(func.lower(Usuarios.correo) == correo).first()
        if not usuario:
            return response_error("Correo o contraseña incorrectos", 401)

        password = data['Contrasena']
        password_sha = sha256_hex(password)
        password_valid = False

        if check_password_hash(usuario.Contrasena, password):
            password_valid = True
        elif check_password_hash(usuario.Contrasena, password_sha):
            password_valid = True
        elif usuario.Contrasena == password_sha:
            password_valid = True
        elif usuario.Contrasena == password:
            password_valid = True

        if not password_valid:
            return response_error("Correo o contraseña incorrectos", 401)

        # Actualizar a hash seguro si el registro estaba en un formato antiguo
        if not check_password_hash(usuario.Contrasena, password):
            usuario.Contrasena = generate_password_hash(password)
            usuario.save()

        token = generate_token(usuario)
        user_data = serialize_model(usuario, exclude_fields=['Contrasena'])
        user_data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None
        user_data['role'] = normalize_role_name(user_data['rol_nombre'])

        return response_success({
            'token': token,
            'usuario': user_data
        }, "Login exitoso")

    except Exception as e:
        return response_error(str(e), 500)


@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return response_error("Token requerido", 401)

        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return response_success(payload, "Token válido")

    except jwt.ExpiredSignatureError:
        return response_error("Token expirado", 401)
    except jwt.InvalidTokenError:
        return response_error("Token inválido", 401)
