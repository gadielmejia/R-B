import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import jwt as _jwt

from app.routes.auth_bp import normalize_role_name
from app.routes.usuarios_bp import serialize_usuario
from app.models import Usuarios
from app.utils.auth_middleware import admin_required


@pytest.mark.parametrize("entrada,esperado", [
    ("admin", "admin"), ("Administrador", "admin"), ("  ADMIN ", "admin"),
    ("empleado", "empleado"), ("cliente", "user"), ("", "user"), (None, "user"), (123, "user"),
])
def test_unit01_normalize_role_name(entrada, esperado):
    assert normalize_role_name(entrada) == esperado


def _usuario_mock(nombre, correo, rol_nombre):
    usuario = Usuarios(
        nombre=nombre,
        documento="1234567890",
        correo=correo,
        Contrasena="hashed_password",
        idRol=1,
    )
    usuario.idUsuario = 1
    usuario.rol = MagicMock()
    usuario.rol.nombre = rol_nombre
    return usuario


def test_unit02_serialize_usuario_no_expone_contrasena():
    usuario = _usuario_mock("Admin Test", "admin@rentstyle.com", "admin")
    data = serialize_usuario(usuario)
    assert "Contrasena" not in data


def _token(app, rol, expira_en=timedelta(hours=1)):
    payload = {"rol": rol, "exp": datetime.utcnow() + expira_en}
    return _jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def _vista_protegida():
    @admin_required
    def vista():
        return "ok", 200
    return vista


def test_unit03_admin_required_sin_token(app):
    with app.test_request_context("/x"):
        resp, status = _vista_protegida()()
    assert status == 401
    assert resp.get_json()["message"] == "Token de acceso requerido"


def test_unit04_admin_required_rechaza_cliente(app):
    token_cliente = "Bearer " + _token(app, "user")
    with app.test_request_context("/x", headers={"Authorization": token_cliente}):
        resp, status = _vista_protegida()()
    assert status == 403
    assert "rol admin" in resp.get_json()["message"]


def test_unit05_admin_required_rechaza_empleado(app):
    token_empleado = "Bearer " + _token(app, "empleado")
    with app.test_request_context("/x", headers={"Authorization": token_empleado}):
        resp, status = _vista_protegida()()
    assert status == 403


def test_unit06_admin_required_rechaza_token_expirado(app):
    tok = _token(app, "admin", expira_en=timedelta(hours=-1))
    with app.test_request_context("/x", headers={"Authorization": "Bearer " + tok}):
        resp, status = _vista_protegida()()
    assert status == 401
    assert "expirada" in resp.get_json()["message"]


def test_unit07_admin_required_acepta_admin(app):
    token_admin = "Bearer " + _token(app, "admin")
    with app.test_request_context("/x", headers={"Authorization": token_admin}):
        assert _vista_protegida()() == ("ok", 200)


def test_unit08_normalize_role_name_valores_vacios():
    assert normalize_role_name("   ") == "user"


def test_unit09_normalize_role_name_mayusculas_mixtas():
    assert normalize_role_name("eMpLeAdO") == "empleado"


def test_unit10_serialize_usuario_mantiene_campos_seguros():
    usuario = _usuario_mock("User Test", "test@rentstyle.com", "user")
    data = serialize_usuario(usuario)
    assert data["correo"] == "test@rentstyle.com"
    assert data["rol_nombre"] == "user"


def test_int01_reporte_rechaza_trimestre_invalido(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "admin")}
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=5", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["message"] == "'quarter' debe estar entre 1 y 4"


def test_int02_reporte_exige_parametro_year(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "admin")}
    response = client.get("/api/reportes/trimestral/excel?quarter=2", headers=headers)
    assert response.status_code == 400
    assert "requeridos" in response.get_json()["message"]


def test_int03_crear_rol_exige_admin(client):
    response = client.post("/api/roles", json={"nombre": "rol_no_autorizado"})
    assert response.status_code in (401, 403)


def test_int04_admin_flujo_completo_reporte_valido(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "admin")}
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=2", headers=headers)
    assert response.status_code == 200


def test_int05_login_exitoso(client):
    response = client.post("/api/login", json={"correo": "admin@rentstyle.com", "Contrasena": "admin123"})
    body = response.get_json()
    assert response.status_code == 200
    assert body["data"]["usuario"]["correo"] == "admin@rentstyle.com"
    assert body["data"]["usuario"]["role"] == "admin"
    assert body["data"]["usuario"]["rol_nombre"] in ("Administrador", "admin")
    assert "token" in body["data"]


def test_int06_login_con_contrasena_incorrecta(client):
    response = client.post("/api/login", json={"correo": "admin@rentstyle.com", "Contrasena": "password-mala"})
    assert response.status_code == 401
    assert response.get_json()["message"] == "Correo o contraseña incorrectos"


def test_int07_verificar_token_valido(client, app):
    token = _token(app, "admin")
    response = client.get("/api/verify-token", headers={"Authorization": "Bearer " + token})
    body = response.get_json()
    assert response.status_code == 200
    assert body["data"]["rol"] == "admin"


def test_int08_verificar_token_invalido(client):
    response = client.get("/api/verify-token", headers={"Authorization": "Bearer token-invalido"})
    assert response.status_code == 401
    assert response.get_json()["message"] == "Token inválido"


def test_int09_listar_usuarios_retorna_usuarios(client):
    response = client.get("/api/usuarios")
    body = response.get_json()
    assert response.status_code == 200
    assert isinstance(body["data"], list)
    assert any(usuario["correo"] == "admin@rentstyle.com" for usuario in body["data"])


def test_int10_crear_usuario_rechaza_documento_duplicado(client):
    payload = {
        "nombre": "Duplicado Doc",
        "documento": "1000000001",
        "correo": "duplicado.doc@rentstyle.com",
        "Contrasena": "Password123!",
    }
    response = client.post("/api/usuarios", json=payload)
    assert response.status_code == 400
    assert "El documento ya está registrado" in response.get_json()["message"]


def test_int11_crear_usuario_rechaza_correo_duplicado(client):
    email = "correo.dup@rentstyle.com"
    first_payload = {
        "nombre": "Correo Duplicado",
        "documento": "1098765432",
        "correo": email,
        "Contrasena": "Password123!",
    }
    first_response = client.post("/api/usuarios", json=first_payload)
    assert first_response.status_code == 201

    duplicate_payload = {
        "nombre": "Otro Correo Duplicado",
        "documento": "1098765433",
        "correo": email.upper(),
        "Contrasena": "Password123!",
    }
    response = client.post("/api/usuarios", json=duplicate_payload)
    assert response.status_code == 400
    assert "El correo ya está registrado" in response.get_json()["message"]


def test_int12_registro_publico_fuerza_rol_cliente(client):
    payload = {
        "nombre": "Intruso",
        "documento": "5555555555",
        "correo": "intruso@test.com",
        "Contrasena": "Password123!",
        "idRol": 1,
    }
    response = client.post("/api/usuarios", json=payload)
    body = response.get_json()
    assert response.status_code == 201
    assert body["data"]["rol_nombre"].lower() == "cliente"
    assert body["data"]["idRol"] == 2


def test_int13_get_roles_lista_sin_admin(client):
    response = client.get("/api/roles")
    body = response.get_json()
    assert response.status_code == 200
    assert isinstance(body["data"], list)
    assert any(rol["nombre"] == "Administrador" for rol in body["data"])


def test_int14_crear_rol_con_admin(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "admin")}
    response = client.post("/api/roles", json={"nombre": "Analista"}, headers=headers)
    body = response.get_json()
    assert response.status_code == 201
    assert body["data"]["nombre"] == "Analista"


def test_int15_crear_rol_duplicado_rechaza_admin(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "admin")}
    response = client.post("/api/roles", json={"nombre": "Administrador"}, headers=headers)
    assert response.status_code == 400
    assert response.get_json()["message"] == "El rol ya existe"


def test_int16_reporte_rechaza_empleado(client, app):
    headers = {"Authorization": "Bearer " + _token(app, "empleado")}
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=2", headers=headers)
    assert response.status_code == 403
    assert "rol admin" in response.get_json()["message"]

