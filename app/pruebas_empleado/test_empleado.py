import jwt
import re
import pytest

#Pruebas Unitarias

from werkzeug.security import check_password_hash
from app.routes.auth_bp import (
    normalize_role_name,
    is_sha256_hash,
    hash_password
)

from app.routes.usuarios_bp import (
    normalize_password,
    is_sha256_hash as users_is_sha256_hash
)


# 1. Normalizar rol administrador
def test_normalizar_rol_administrador():
    rol = "Admin"

    resultado = normalize_role_name(rol)

    assert resultado == "admin"


# 2. Normalizar rol administrador con espacios
def test_normalizar_rol_administrador_con_espacios():
    rol = "  ADMINISTRADOR  "

    resultado = normalize_role_name(rol)

    assert resultado == "admin"
    assert resultado.islower()


# 3. Reconocer rol empleado
def test_reconocer_rol_empleado():
    rol = "Empleado"

    resultado = normalize_role_name(rol)

    assert resultado == "empleado"
    assert resultado != "admin"


# 4. Normalizar rol cliente
def test_normalizar_rol_cliente():
    rol = "Cliente"

    resultado = normalize_role_name(rol)

    assert resultado == "user"


# 5. Validar rol nulo
def test_validar_rol_nulo():
    rol = None

    resultado = normalize_role_name(rol)

    assert resultado == "user"


# 6. Validar diferentes nombres de roles
@pytest.mark.parametrize("rol,esperado", [
    ("Admin", "admin"),
    ("ADMIN", "admin"),
    ("Administrador", "admin"),
    ("Empleado", "empleado"),
    ("EMPLEADO", "empleado"),
    ("Cliente", "user"),
    ("Usuario", "user")
])
def test_validar_diferentes_nombres_de_roles(rol, esperado):
    resultado = normalize_role_name(rol)

    assert resultado == esperado


# 7. Identificar hash SHA-256 válido
def test_identificar_hash_sha256_valido():
    contraseña_hash = "a" * 64

    resultado = is_sha256_hash(contraseña_hash)

    assert resultado is True
    assert len(contraseña_hash) == 64


# 8. Rechazar hash con longitud incorrecta
def test_rechazar_hash_con_longitud_incorrecta():
    contraseña_hash = "abc123"

    resultado = is_sha256_hash(contraseña_hash)

    assert resultado is False


# 9. Rechazar hash con caracteres inválidos
def test_rechazar_hash_con_caracteres_invalidos():
    contraseña_hash = "g" * 64

    resultado = users_is_sha256_hash(contraseña_hash)

    assert resultado is False


# 10. Generar hash de contraseña
def test_generar_hash_de_contrasena():
    contraseña = "Empleado123!"

    resultado = hash_password(contraseña)

    assert isinstance(resultado, str)
    assert len(resultado) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", resultado)
    assert resultado != contraseña


# 11. Normalizar contraseña en texto plano
def test_normalizar_contrasena_texto_plano():
    contraseña = "Empleado123!"

    resultado = normalize_password(contraseña)

    assert isinstance(resultado, str)
    assert resultado.startswith("scrypt:")
    assert resultado != contraseña
    assert check_password_hash(resultado, contraseña) is True


# 12. Conservar contraseña SHA-256
def test_conservar_contrasena_sha256():
    contraseña_hash = "b" * 64

    resultado = normalize_password(contraseña_hash)

    assert resultado == contraseña_hash
    assert users_is_sha256_hash(resultado) is True


# 13. Validar contraseña vacía
def test_validar_contrasena_vacia():
    contraseña = ""

    resultado = normalize_password(contraseña)

    assert resultado == ""


# 14. Validar contraseña nula
def test_validar_contrasena_nula():
    contraseña = None

    resultado = normalize_password(contraseña)

    assert resultado is None
    
#Pruebas de Integración

from app.database.database import db
from app.models.inventario import Inventario
from app.models.reserva import Reserva
from app.models.usuarios import Usuarios
from app.pruebas_empleado.conftest import PASS_EMPLEADO, SECRET


# INT-EMP-01: login HTTP + consulta de usuario + generación de token JWT.
def test_integracion_login_empleado(client):
    response = client.post(
        "/api/login",
        json={"correo": "empleado@rentstyle.com", "Contrasena": PASS_EMPLEADO},
    )

    assert response.status_code == 200
    body = response.get_json()["data"]
    payload = jwt.decode(body["token"], SECRET, algorithms=["HS256"])
    assert payload["rol"] == "empleado"
    assert body["usuario"]["role"] == "empleado"
    assert "Contrasena" not in body["usuario"]


# INT-EMP-02: petición del empleado + creación del usuario + persistencia en BD.
def test_integracion_empleado_crea_cliente(client, app, headers_empleado):
    response = client.post(
        "/api/usuarios",
        json={
            "nombre": "Cliente Integracion",
            "documento": "9000000001",
            "correo": "cliente.integracion@test.com",
            "Contrasena": "Cliente123!",
            "idRol": 1,
        },
        headers=headers_empleado,
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["idRol"] == 2
    assert data["rol_nombre"].lower() == "cliente"

    with app.app_context():
        saved = Usuarios.query.filter_by(correo="cliente.integracion@test.com").first()
        assert saved is not None
        assert saved.idRol == 2


# INT-EMP-03: petición PUT + actualización del inventario + persistencia en BD.
def test_integracion_empleado_actualiza_estado_inventario(client, app, headers_empleado):
    response = client.put(
        "/api/inventario/1",
        json={"estado": "Reparacion"},
        headers=headers_empleado,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["estado"] == "Reparacion"

    with app.app_context():
        item = db.session.get(Inventario, 1)
        assert item is not None
        assert item.estado == "Reparacion"


# INT-EMP-04: actualización de reserva + lectura de detalle + sincronización de inventario.
def test_integracion_empleado_confirma_reserva_y_actualiza_inventario(
    client, app, headers_empleado
):
    response = client.put(
        "/api/reservas/1",
        json={"estado": "Confirmada"},
        headers=headers_empleado,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["estado"] == "Confirmada"

    with app.app_context():
        reserva = db.session.get(Reserva, 1)
        inventario = db.session.get(Inventario, 2)
        assert reserva.estado == "Confirmada"
        assert inventario.estado == "Alquilado"
