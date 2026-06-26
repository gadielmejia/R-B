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

FRONTEND — 4 archivos

Archivo 1: src/utils/api.js — archivo nuevo

Crea este archivo en src/utils/api.js:

jsconst BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.clear();
    window.location.href = '/login';
    return null;
  }

  return res;
}

export const api = {
  get: (path) => apiFetch(path),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => apiFetch(path, { method: 'DELETE' }),
};