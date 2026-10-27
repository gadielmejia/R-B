import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config.settings import Config
from app.database.database import db
from app.models.roles import Roles
from app.models.usuarios import Usuarios


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setattr(Config, "SECRET_KEY", "test-secret-key-rentstyle")
    monkeypatch.setattr(Config, "CLOUDINARY_CLOUD_NAME", "demo")
    monkeypatch.setattr(Config, "CLOUDINARY_API_KEY", "123456")
    monkeypatch.setattr(Config, "CLOUDINARY_API_SECRET", "secreto-de-prueba")
    app = create_app()
    app.config.update({"TESTING": True, "SECRET_KEY": "test-secret-key-rentstyle"})

    with app.app_context():
        assert str(db.engine.url).startswith("sqlite"), "Las pruebas no deben tocar MySQL"
        db.create_all()
        db.session.add_all([
            Roles(idRol=1, nombre="Administrador"),
            Roles(idRol=2, nombre="Cliente"),
            Roles(idRol=3, nombre="Empleado"),
        ])
        db.session.add(Usuarios(
            nombre="Admin Test",
            documento="1000000001",
            correo="admin@rentstyle.com",
            Contrasena=generate_password_hash("admin123"),
            idRol=1,
        ))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
