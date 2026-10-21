import pytest
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.database.database import db
from app.models.roles import Roles
from app.models.usuarios import Usuarios
from app.routes.auth_bp import normalize_role_name, generate_token
from app.routes.usuarios_bp import serialize_usuario
from app.utils.auth_middleware import admin_required


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
        rol_admin = Roles(idRol=1, nombre="Administrador")
        rol_cliente = Roles(idRol=2, nombre="Cliente")
        rol_empleado = Roles(idRol=3, nombre="Empleado")
        db.session.add_all([rol_admin, rol_cliente, rol_empleado])
        db.session.commit()

        admin_user = Usuarios(
            nombre="Admin Test",
            documento="1000000001",
            correo="admin@rentstyle.com",
            Contrasena=generate_password_hash("admin123"),
            idRol=1,
        )
        cliente_user = Usuarios(
            nombre="Juan Perez",
            documento="1020304050",
            correo="juan@test.com",
            Contrasena=generate_password_hash("Test1234!"),
            idRol=2,
        )
        db.session.add_all([admin_user, cliente_user])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# UNIT-01: Normalización de nombres de rol
@pytest.mark.parametrize("entrada,esperado", [
    ("admin", "admin"),
    ("  ADMIN ", "admin"),
    ("Administrador", "admin"),
    ("empleado", "empleado"),
    ("  Empleado  ", "empleado"),
    ("cliente", "user"),
    ("", "user"),
    (None, "user"),
    (123, "user"),
])
def test_unit01_normalize_role_name(entrada, esperado):
    # Arrange & Act
    resultado = normalize_role_name(entrada)
    # Assert
    assert resultado == esperado


# UNIT-02: No exponer el hash de la contraseña al serializar usuario (Falla por BUG-SEC-002)
def test_unit02_serialize_usuario_no_expone_contrasena(app):
    with app.app_context():
        # Arrange
        usuario = Usuarios.query.filter_by(correo="admin@rentstyle.com").first()
        # Act
        data = serialize_usuario(usuario)
        # Assert
        assert "Contrasena" not in data, "BUG-SEC-002: Se está exponiendo el hash de la contraseña"


# UNIT-03: Validación de campos requeridos al crear usuario
def test_unit03_crear_usuario_campos_requeridos(client):
    # Arrange
    payload = {
        "nombre": "Carlos Ruiz",
        "documento": "   ",  # Vacío con espacios
        "correo": "carlos@test.com",
        "Contrasena": "Password123!"
    }
    # Act
    response = client.post("/api/usuarios", json=payload)
    body = response.get_json()
    # Assert
    assert response.status_code == 400
    assert "El campo 'documento' es requerido" in body["message"]


# UNIT-04: Rechazo de documento y correo duplicados (case-insensitive)
def test_unit04_crear_usuario_rechaza_duplicados(client):
    # Arrange: juan@test.com y doc 1020304050 ya existen en el fixture
    payload_correo_dup = {
        "nombre": "Otro Juan",
        "documento": "9999999999",
        "correo": "  JUAN@TEST.COM ",
        "Contrasena": "Password123!"
    }
    # Act
    res_correo = client.post("/api/usuarios", json=payload_correo_dup)
    # Assert
    assert res_correo.status_code == 400
    assert "El correo ya está registrado" in res_correo.get_json()["message"]


# UNIT-05: Rechazo de contraseña enviada como hash SHA-256
def test_unit05_crear_usuario_rechaza_hash_sha256(client):
    # Arrange
    fake_sha256 = "a" * 64
    payload = {
        "nombre": "Ana Gomez",
        "documento": "1099887766",
        "correo": "ana@test.com",
        "Contrasena": fake_sha256
    }
    # Act
    response = client.post("/api/usuarios", json=payload)
    # Assert
    assert response.status_code == 400
    assert "La contraseña debe ser texto plano, no el hash" in response.get_json()["message"]


# UNIT-06: Asignación forzada de rol Cliente en registro público sin token de Admin
def test_unit06_registro_publico_fuerza_rol_cliente(client):
    # Arrange: Intenta inyectar idRol = 1 (Administrador) sin estar autenticado
    payload = {
        "nombre": "Intruso",
        "documento": "5555555555",
        "correo": "intruso@test.com",
        "Contrasena": "Password123!",
        "idRol": 1
    }
    # Act
    response = client.post("/api/usuarios", json=payload)
    data = response.get_json()["data"]
    # Assert
    assert response.status_code == 201
    assert data["rol_nombre"].lower() == "cliente"
    assert data["idRol"] == 2


# UNIT-07: Escalada de privilegios en PUT /api/usuarios/<id> sin token (Falla por BUG-SEC-003)
def test_unit07_actualizar_usuario_bloquea_escalada_rol_sin_token(client, app):
    with app.app_context():
        cliente = Usuarios.query.filter_by(correo="juan@test.com").first()
        user_id = cliente.idUsuario

    # Arrange & Act: Petición PUT sin token intentando pasar a idRol=1 (Admin)
    response = client.put(f"/api/usuarios/{user_id}", json={"idRol": 1})

    # Assert: El oráculo exige 401 o 403, pero actualmente devuelve 200 (BUG-SEC-003)
    assert response.status_code in (401, 403), "BUG-SEC-003: Escalada de privilegios permitida sin token"


# UNIT-08: Generación de token JWT y verificación en /api/verify-token
def test_unit08_generate_and_verify_token(client, app):
    with app.app_context():
        # Arrange
        cliente = Usuarios.query.filter_by(correo="juan@test.com").first()
        token = generate_token(cliente)

    # Act
    response = client.get("/api/verify-token", headers={"Authorization": f"Bearer {token}"})
    body = response.get_json()

    # Assert
    assert response.status_code == 200
    assert body["data"]["correo"] == "juan@test.com"
    assert body["data"]["rol"] == "user"


# UNIT-09: Middleware admin_required rechaza peticiones sin token o con token expirado
def test_unit09_admin_required_sin_token_y_expirado(app):
    @admin_required
    def dummy_view():
        return ("ok", 200)

    # Caso A: Sin token
    with app.test_request_context("/ruta-protegida", headers={}):
        res_no_token, status_no_token = dummy_view()
        assert status_no_token == 401
        assert "Token de acceso requerido" in res_no_token.get_json()["message"]

    # Caso B: Token expirado hace 1 hora
    with app.app_context():
        expired_token = jwt.encode(
            {"idUsuario": 1, "rol": "admin", "exp": datetime.utcnow() - timedelta(hours=1)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
    with app.test_request_context("/ruta-protegida", headers={"Authorization": f"Bearer {expired_token}"}):
        res_exp, status_exp = dummy_view()
        assert status_exp == 401
        assert "Sesión expirada" in res_exp.get_json()["message"]


# UNIT-10: Middleware admin_required valida roles (rechaza cliente/empleado y acepta admin)
def test_unit10_admin_required_control_de_roles(app):
    @admin_required
    def dummy_view():
        return ("ok", 200)

    with app.app_context():
        token_user = jwt.encode({"idUsuario": 2, "rol": "user"}, app.config["SECRET_KEY"], algorithm="HS256")
        token_emp = jwt.encode({"idUsuario": 3, "rol": "empleado"}, app.config["SECRET_KEY"], algorithm="HS256")
        token_adm = jwt.encode({"idUsuario": 1, "rol": "admin"}, app.config["SECRET_KEY"], algorithm="HS256")

    # Cliente -> 403
    with app.test_request_context("/admin", headers={"Authorization": f"Bearer {token_user}"}):
        _, status_user = dummy_view()
        assert status_user == 403

    # Empleado -> 403
    with app.test_request_context("/admin", headers={"Authorization": f"Bearer {token_emp}"}):
        _, status_emp = dummy_view()
        assert status_emp == 403

    # Admin -> 200
    with app.test_request_context("/admin", headers={"Authorization": f"Bearer {token_adm}"}):
        res_adm, status_adm = dummy_view()
        assert status_adm == 200
        assert res_adm == "ok"