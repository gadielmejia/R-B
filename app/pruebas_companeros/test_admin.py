from datetime import datetime, timedelta
 
import jwt as _jwt
import pytest
from flask import Flask
 
from app.config.settings import Config
from app.models.roles import Roles
from app.models.usuarios import Usuarios
from app.routes.auth_bp import normalize_role_name
from app.routes.usuarios_bp import serialize_usuario
from app.utils.auth_middleware import admin_required
 
SECRET = "test-secret-key-rentstyle"
 

@pytest.fixture
def app_minima(monkeypatch):
    """Mini-app Flask: solo SECRET_KEY y contexto de request. Sin BD ni blueprints."""
    monkeypatch.setattr(Config, "SECRET_KEY", SECRET)
    mini = Flask(__name__)
    mini.config["SECRET_KEY"] = SECRET
    return mini
 
 
def _token(rol, expira_en=timedelta(hours=1), clave=SECRET):
    payload = {"rol": rol, "exp": datetime.utcnow() + expira_en}
    return _jwt.encode(payload, clave, algorithm="HS256")
 
 
def _vista_protegida():
    @admin_required
    def vista():
        return "ok", 200
    return vista
 
 
def _usuario_en_memoria(nombre, correo, rol_nombre, id_rol):
    """Objetos del modelo creados en memoria: no hay sesión, no hay BD."""
    usuario = Usuarios(
        nombre=nombre,
        documento="1000000001",
        correo=correo,
        Contrasena="hash_super_secreto",
        idRol=id_rol,
    )
    usuario.idUsuario = 1
    usuario.rol = Roles(idRol=id_rol, nombre=rol_nombre)
    return usuario
 

@pytest.mark.parametrize("entrada,esperado", [
    ("admin", "admin"),
    ("Administrador", "admin"),
    ("  ADMIN ", "admin"),
    ("empleado", "empleado"),
    ("cliente", "user"),
    ("", "user"),
    (None, "user"),
    (123, "user"),
])
def test_unit01_normalize_role_name(entrada, esperado):
    # Arrange: entrada y esperado vienen de la parametrización
    # Act
    resultado = normalize_role_name(entrada)
    # Assert
    assert resultado == esperado
 
 
def test_unit02_serialize_usuario_no_expone_contrasena():
    # Arrange
    usuario = _usuario_en_memoria("Admin Test", "admin@rentstyle.com", "Administrador", 1)
    # Act
    data = serialize_usuario(usuario)
    # Assert
    assert "Contrasena" not in data
 
 
def test_unit03_admin_required_sin_token(app_minima):
    # Arrange
    vista = _vista_protegida()
    # Act
    with app_minima.test_request_context("/x"):
        resp, status = vista()
        mensaje = resp.get_json()["message"]
    # Assert
    assert status == 401
    assert mensaje == "Token de acceso requerido"
 
 
def test_unit04_admin_required_rechaza_cliente(app_minima):
    # Arrange
    vista = _vista_protegida()
    headers = {"Authorization": "Bearer " + _token("user")}
    # Act
    with app_minima.test_request_context("/x", headers=headers):
        resp, status = vista()
        mensaje = resp.get_json()["message"]
    # Assert
    assert status == 403
    assert "rol admin" in mensaje
 
 
def test_unit05_admin_required_rechaza_empleado(app_minima):
    # Arrange
    vista = _vista_protegida()
    headers = {"Authorization": "Bearer " + _token("empleado")}
    # Act
    with app_minima.test_request_context("/x", headers=headers):
        resp, status = vista()
    # Assert
    assert status == 403
 
 
def test_unit06_admin_required_rechaza_token_expirado(app_minima):
    # Arrange
    vista = _vista_protegida()
    headers = {"Authorization": "Bearer " + _token("admin", expira_en=timedelta(hours=-1))}
    # Act
    with app_minima.test_request_context("/x", headers=headers):
        resp, status = vista()
        mensaje = resp.get_json()["message"]
    # Assert
    assert status == 401
    assert "expirada" in mensaje
 
 
def test_unit07_admin_required_acepta_admin(app_minima):
    # Arrange
    vista = _vista_protegida()
    headers = {"Authorization": "Bearer " + _token("admin")}
    # Act
    with app_minima.test_request_context("/x", headers=headers):
        resultado = vista()
    # Assert
    assert resultado == ("ok", 200)
 
 
def test_unit08_normalize_role_name_valores_vacios():
    # Arrange
    entrada = "   "
    # Act
    resultado = normalize_role_name(entrada)
    # Assert
    assert resultado == "user"
 
 
def test_unit09_normalize_role_name_mayusculas_mixtas():
    # Arrange
    entrada = "eMpLeAdO"
    # Act
    resultado = normalize_role_name(entrada)
    # Assert
    assert resultado == "empleado"
 
 
def test_unit10_serialize_usuario_mantiene_campos_seguros():
    # Arrange
    usuario = _usuario_en_memoria("Admin Test", "admin@rentstyle.com", "Administrador", 1)
    # Act
    data = serialize_usuario(usuario)
    # Assert
    assert data["correo"] == "admin@rentstyle.com"
    assert data["rol_nombre"] == "Administrador"


def _headers_admin(app):
    return {"Authorization": "Bearer " + _token("admin", clave=app.config["SECRET_KEY"])}
 
 
def test_int01_reporte_rechaza_trimestre_invalido(client, app):
    # Arrange
    headers = _headers_admin(app)
    # Act
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=5", headers=headers)
    # Assert
    assert response.status_code == 400
    assert response.get_json()["message"] == "'quarter' debe estar entre 1 y 4"
 
 
def test_int02_reporte_exige_parametro_year(client, app):
    # Arrange
    headers = _headers_admin(app)
    # Act
    response = client.get("/api/reportes/trimestral/excel?quarter=2", headers=headers)
    # Assert
    assert response.status_code == 400
    assert "requeridos" in response.get_json()["message"]
 
 
def test_int03_crear_rol_exige_admin(client):
    # Arrange
    payload = {"nombre": "rol_no_autorizado"}
    # Act
    response = client.post("/api/roles", json=payload)
    # Assert
    assert response.status_code in (401, 403)
 
 
def test_int04_admin_flujo_completo_reporte_valido(client, app):
    # Arrange
    headers = _headers_admin(app)
    # Act
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=2", headers=headers)
    # Assert
    assert response.status_code == 200
