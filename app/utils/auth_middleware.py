from functools import wraps
from flask import request, current_app
from app.utils.response import response_error
import jwt


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return response_error("Token de acceso requerido", 401)
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return response_error("Sesión expirada, inicia sesión nuevamente", 401)
        except jwt.InvalidTokenError:
            return response_error("Token inválido", 401)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return response_error("Token de acceso requerido", 401)
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('rol') != 'admin':
                return response_error("Acceso denegado: se requiere rol admin", 403)
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return response_error("Sesión expirada, inicia sesión nuevamente", 401)
        except jwt.InvalidTokenError:
            return response_error("Token inválido", 401)
        return f(*args, **kwargs)
    return decorated

