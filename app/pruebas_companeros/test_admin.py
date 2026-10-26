import pytest
from app.routes.auth_bp import normalize_role_name
from app.routes.usuarios_bp import serialize_usuario
from app.models import Usuarios, Inventario
 

@pytest.mark.parametrize("entrada,esperado", [
    ("admin", "admin"), ("Administrador", "admin"), ("  ADMIN ", "admin"),
    ("empleado", "empleado"), ("cliente", "user"), ("", "user"), (None, "user"), (123, "user"),
])
def test_unit01_normalize_role_name(entrada, esperado):
    assert normalize_role_name(entrada) == esperado
 

def test_unit02_serialize_usuario_no_expone_contrasena(app):
    with app.app_context():
        u = Usuarios.query.filter_by(correo="admin@rentstyle.com").first()
        data = serialize_usuario(u)
        assert "Contrasena" not in data, "La respuesta incluye el hash de la contraseña"
 

from datetime import datetime, timedelta
import jwt as _jwt
from app.utils.auth_middleware import admin_required
 
 
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
    with app.test_request_context("/x", headers={"Authorization": "Bearer " + _token(app, "user")}):
        resp, status = _vista_protegida()()
    assert status == 403
    assert "rol admin" in resp.get_json()["message"]
 
 
def test_unit05_admin_required_rechaza_empleado(app):
    with app.test_request_context("/x", headers={"Authorization": "Bearer " + _token(app, "empleado")}):
        resp, status = _vista_protegida()()
    assert status == 403
 
 
def test_unit06_admin_required_rechaza_token_expirado(app):
    tok = _token(app, "admin", expira_en=timedelta(hours=-1))
    with app.test_request_context("/x", headers={"Authorization": "Bearer " + tok}):
        resp, status = _vista_protegida()()
    assert status == 401
    assert "expirada" in resp.get_json()["message"]
 
 
def test_unit07_admin_required_acepta_admin(app):
    with app.test_request_context("/x", headers={"Authorization": "Bearer " + _token(app, "admin")}):
        assert _vista_protegida()() == ("ok", 200)
 
 
def test_unit08_reporte_rechaza_trimestre_invalido(client, app):
    h = {"Authorization": "Bearer " + _token(app, "admin")}
    r = client.get("/api/reportes/trimestral/excel?year=2026&quarter=5", headers=h)
    assert r.status_code == 400
    assert r.get_json()["message"] == "'quarter' debe estar entre 1 y 4"
 
 
def test_unit09_reporte_exige_parametro_year(client, app):
    h = {"Authorization": "Bearer " + _token(app, "admin")}
    r = client.get("/api/reportes/trimestral/excel?quarter=2", headers=h)
    assert r.status_code == 400
    assert "requeridos" in r.get_json()["message"]
 
 
def test_unit10_crear_rol_exige_admin(client):
    r = client.post("/api/roles", json={"nombre": "rol_no_autorizado"})
    assert r.status_code in (401, 403), "POST /api/roles crea roles sin token ni rol admin"
 

