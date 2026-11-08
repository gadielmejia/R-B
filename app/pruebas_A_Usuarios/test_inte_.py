"""
Módulo de Pruebas de Integración: Registro, Login y Tokens JWT (RF01, RF02)
Responsable: Stiven Alejandro Sáchica Triviño
Proyecto: RentStyle (Backend R-B)
Estándar: Caja Gris / Integración API REST + Base de Datos
"""

import pytest
from app import create_app
from app.database.database import db
from app.models.roles import Roles
from app.models.usuarios import Usuarios
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-rentstyle",
    })
    with app.app_context():
        db.create_all()
        # Sembrar rol Cliente necesario para el registro público
        rol_cliente = Roles(idRol=2, nombre="Cliente")
        db.session.add(rol_cliente)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# INT-01: Registro de usuario y persistencia real en Base de Datos con validación de duplicados
# ==============================================================================
def test_int01_registro_y_persistencia(client, app):
    # Arrange: Datos de un nuevo usuario
    payload = {
        "nombre": "Sofia Martinez",
        "documento": "1030405060",
        "correo": "Sofia@Test.com",  # Con mayúsculas para probar normalización
        "Contrasena": "Pass1234!"
    }

    # Act 1: Enviar solicitud de registro
    response = client.post("/api/usuarios", json=payload)
    data = response.get_json()

    # Assert 1: Verificar respuesta exitosa 201
    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["data"]["correo"] == "sofia@test.com"  # Normalizado a minúsculas

    # Act 2: Intentar registrar el mismo documento nuevamente (Prueba de duplicados)
    response_dup = client.post("/api/usuarios", json=payload)
    
    # Assert 2: Verificar rechazo 400 por duplicidad de documento en la BD
    assert response_dup.status_code == 400
    assert "El documento ya está registrado" in response_dup.get_json()["message"]


# ==============================================================================
# INT-02: Inicio de sesión exitoso (Login) generando token JWT
# ==============================================================================
def test_int02_login_exitoso_genera_jwt(client, app):
    with app.app_context():
        # Arrange: Sembrar un usuario directamente en la BD de pruebas
        usuario = Usuarios(
            nombre="Andres Parra",
            documento="1040506070",
            correo="andres@test.com",
            Contrasena=generate_password_hash("Secreto123!"),
            idRol=2
        )
        db.session.add(usuario)
        db.session.commit()

    # Arrange: Credenciales correctas para el login
    credenciales = {
        "correo": "andres@test.com",
        "Contrasena": "Secreto123!"
    }

    # Act: Enviar petición POST al login
    response = client.post("/api/login", json=credenciales)
    body = response.get_json()

    # Assert: Validar código 200 y recepción del token JWT
    assert response.status_code == 200
    assert "token" in body["data"]
    assert body["data"]["usuario"]["correo"] == "andres@test.com"


# ==============================================================================
# INT-03: Rechazo de inicio de sesión con credenciales incorrectas
# ==============================================================================
def test_int03_login_credenciales_incorrectas(client):
    # Arrange: Credenciales erróneas
    credenciales = {
        "correo": "inexistente@test.com",
        "Contrasena": "ClaveFalsa"
    }

    # Act: Enviar petición de login
    response = client.post("/api/login", json=credenciales)
    body = response.get_json()

    # Assert: Validar código 401 Unauthorized
    assert response.status_code == 401
    assert "Correo o contraseña incorrectos" in body["message"]


# ==============================================================================
# INT-04: Validación de token JWT en endpoint protegido (/api/verify-token)
# ==============================================================================
def test_int04_verificacion_token_jwt(client, app):
    with app.app_context():
        # Arrange: Crear usuario y generar token de sesión
        usuario = Usuarios(
            nombre="Lucia Gomez",
            documento="1050607080",
            correo="lucia@test.com",
            Contrasena=generate_password_hash("Lucia123!"),
            idRol=2
        )
        db.session.add(usuario)
        db.session.commit()
        
        from app.routes.auth_bp import generate_token
        token = generate_token(usuario)

    # Act: Enviar token en los Headers de la petición GET
    response = client.get(
        "/api/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    body = response.get_json()

    # Assert: Validar que el token sea reconocido como válido (200 OK)
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["correo"] == "lucia@test.com"