from flask import Blueprint, request
from app.database.database import db
from app.models.usuarios import Usuarios
from app.utils.response import response_success, response_error, serialize_model

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'correo' not in data or 'Contrasena' not in data:
            return response_error("Correo y contraseña son requeridos", 400)

        usuario = Usuarios.query.filter_by(correo=data['correo']).first()
        if not usuario or usuario.Contrasena != data['Contrasena']:
            return response_error("Correo o contraseña incorrectos", 401)

        user_data = serialize_model(usuario)
        user_data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None

        return response_success(user_data, "Login exitoso")
    except Exception as e:
        return response_error(str(e), 500)