import os
os.environ["CLOUDINARY_URL"] = "cloudinary://test_key:test_secret@test_cloud"
os.environ["SECRET_KEY"] = "test-secret-key-rentstyle"

from app.config.settings import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

import pytest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.database.database import db
from app.models.roles import Roles
from app.models.usuarios import Usuarios
from app.models.categoria import Categoria
from app.models.prenda import Prenda
from app.models.inventario import Inventario
from app.models.lote import Lote


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-rentstyle",
        "CLOUDINARY_URL": "cloudinary://test_key:test_secret@test_cloud",
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
