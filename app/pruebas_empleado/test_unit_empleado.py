import jwt
import pytest
 
from app.database.database import db
from app.models.inventario import Inventario
from app.models.reserva import Reserva
from app.models.usuarios import Usuarios
from app.pruebas_empleado.conftest import PASS_EMPLEADO, SECRET
 
 
# ---------------------------------------------------------------- AUTENTICACIÓN
# UNIT-21: login del empleado entrega token con rol 'empleado'
def test_unit21_login_empleado_exitoso(client):
    # Arrange: correo con mayúsculas y espacios + contraseña correcta
    body = {"correo": "  EMPLEADO@rentstyle.com ", "Contrasena": PASS_EMPLEADO}
    # Act
    r = client.post("/api/login", json=body)
    # Assert
    assert r.status_code == 200
    data = r.get_json()["data"]
    payload = jwt.decode(data["token"], SECRET, algorithms=["HS256"])
    assert payload["rol"] == "empleado"
    assert data["usuario"]["role"] == "empleado"
    assert "Contrasena" not in data["usuario"]
 
 
# UNIT-22: login del empleado con credenciales inválidas
@pytest.mark.parametrize("correo,clave", [
    ("empleado@rentstyle.com", "ClaveIncorrecta9"),   # contraseña errónea
    ("noexiste@rentstyle.com", PASS_EMPLEADO),        # correo inexistente
])
def test_unit22_login_empleado_credenciales_invalidas(client, correo, clave):
    # Act
    r = client.post("/api/login", json={"correo": correo, "Contrasena": clave})
    # Assert: mismo mensaje en ambos casos (no revela si el correo existe)
    assert r.status_code == 401
    assert r.get_json()["message"] == "Correo o contraseña incorrectos"
    assert "token" not in str(r.get_json())
 
 
# ---------------------------------------------------------------- GESTIÓN DE USUARIOS
# UNIT-23: el empleado no puede crear administradores (idRol enviado se ignora)
def test_unit23_empleado_crea_usuario_siempre_como_cliente(client, headers_empleado):
    # Arrange
    body = {"nombre": "Nuevo Admin", "documento": "7777777777", "correo": "nuevo@test.com",
            "Contrasena": "Password123!", "idRol": 1}
    # Act
    r = client.post("/api/usuarios", json=body, headers=headers_empleado)
    # Assert
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["idRol"] == 2
    assert data["rol_nombre"] == "Cliente"
 
 
# UNIT-24: el empleado no puede cambiar el rol de un usuario a Administrador
def test_unit24_empleado_no_puede_asignar_rol_admin(client, app, headers_empleado):
    # Act: PUT con token de empleado pidiendo idRol = 1 sobre el cliente Juan
    with app.app_context():
        id_juan = Usuarios.query.filter_by(correo="juan@test.com").first().idUsuario
    r = client.put(f"/api/usuarios/{id_juan}", json={"idRol": 1}, headers=headers_empleado)
    # Assert
    assert r.status_code in (401, 403), "Un empleado convirtió a un cliente en Administrador"
    with app.app_context():
        assert db.session.get(Usuarios, id_juan).idRol == 2
 
 
# UNIT-25: el empleado no puede eliminar la cuenta de un Administrador
def test_unit25_empleado_no_puede_eliminar_administrador(client, app, headers_empleado):
    # Arrange: segundo administrador (sin reservas) para que el DELETE no falle por llaves foráneas
    with app.app_context():
        id_admin = Usuarios.query.filter_by(correo="admin2@rentstyle.com").first().idUsuario
    # Act
    r = client.delete(f"/api/usuarios/{id_admin}", headers=headers_empleado)
    # Assert
    assert r.status_code in (401, 403), "Un empleado eliminó la cuenta de un Administrador"
    with app.app_context():
        assert db.session.get(Usuarios, id_admin) is not None
 
 
# ---------------------------------------------------------------- INVENTARIO
# UNIT-26: el empleado marca una prenda en 'Reparacion'
def test_unit26_empleado_cambia_estado_inventario_a_reparacion(client, app, headers_empleado):
    # Act
    r = client.put("/api/inventario/1", json={"estado": "Reparacion"}, headers=headers_empleado)
    # Assert
    assert r.status_code == 200
    assert r.get_json()["data"]["estado"] == "Reparacion"
    with app.app_context():
        assert db.session.get(Inventario, 1).estado == "Reparacion"
 
 
# UNIT-27: estado de inventario inválido es rechazado y no se modifica la prenda
def test_unit27_inventario_rechaza_estado_invalido(client, app, headers_empleado):
    # Act
    r = client.put("/api/inventario/1", json={"estado": "Perdido"}, headers=headers_empleado)
    # Assert
    assert r.status_code == 400
    assert r.get_json()["message"].startswith("Estado inválido")
    with app.app_context():
        assert db.session.get(Inventario, 1).estado == "Disponible"
 
 
# UNIT-28: alta de inventario con datos inválidos (código duplicado / sin código)
@pytest.mark.parametrize("body,mensaje", [
    ({"idPrenda": 1, "codigo_interno": "VES-001"}, "El código interno ya existe"),
    ({"idPrenda": 1}, "El campo 'codigo_interno' es requerido"),
])
def test_unit28_inventario_rechaza_codigo_duplicado_o_faltante(client, app, headers_empleado, body, mensaje):
    # Act
    r = client.post("/api/inventario", json=body, headers=headers_empleado)
    # Assert
    assert r.status_code == 400
    assert r.get_json()["message"] == mensaje
    with app.app_context():
        assert Inventario.query.count() == 2   # no se creó ninguna prenda nueva
 
 
@pytest.mark.parametrize("nuevo_estado,inventario_esperado", [
    ("Confirmada", "Alquilado"),
    ("Cancelada", "Disponible"),
    ("Finalizada", "Disponible"),
    ("Entregada", "Reservado"),     # el código no toca el inventario en este estado
])
def test_unit29_reserva_sincroniza_estado_del_inventario(client, app, headers_empleado,
                                                         nuevo_estado, inventario_esperado):
    # Arrange: reserva #1 Pendiente con la prenda 2 en estado 'Reservado'
    # Act
    r = client.put("/api/reservas/1", json={"estado": nuevo_estado}, headers=headers_empleado)
    # Assert
    assert r.status_code == 200
    with app.app_context():
        assert db.session.get(Reserva, 1).estado == nuevo_estado
        assert db.session.get(Inventario, 2).estado == inventario_esperado
 
 

def test_unit30_reserva_rechaza_estado_invalido(client, app, headers_empleado):

    r = client.put("/api/reservas/1", json={"estado": "Perdida"}, headers=headers_empleado)

    assert r.status_code == 400, "update_reserva acepta cualquier texto como estado"
    with app.app_context():
        assert db.session.get(Reserva, 1).estado == "Pendiente"