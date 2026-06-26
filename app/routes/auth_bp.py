from flask import Blueprint, request, current_app
from app.models.usuarios import Usuarios
from app.utils.response import response_success, response_error, serialize_model
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def generate_token(usuario):
    payload = {
        'idUsuario': usuario.idUsuario,
        'correo': usuario.correo,
        'rol': usuario.rol.nombre if usuario.rol else 'usuario',
        'exp': datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'correo' not in data or 'Contrasena' not in data:
            return response_error("Correo y contraseña son requeridos", 400)

        usuario = Usuarios.query.filter_by(correo=data['correo']).first()
        if not usuario or usuario.Contrasena != data['Contrasena']:
            return response_error("Correo o contraseña incorrectos", 401)

        token = generate_token(usuario)
        user_data = serialize_model(usuario, exclude_fields=['Contrasena'])
        user_data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None

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
