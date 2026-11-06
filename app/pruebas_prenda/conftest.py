from datetime import date, datetime, timedelta

import jwt
import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config.settings import Config
from app.database.database import db
from app.models.categoria import Categoria
from app.models.inventario import Inventario
from app.models.prenda import Prenda
from app.models.roles import Roles
from app.models.usuarios import Usuarios


SECRET = "test-secret-key-rentstyle"


@pytest.fixture
def app(monkeypatch):
    # Arrange global: BD aislada en memoria (nunca MySQL)
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setattr(Config, "SECRET_KEY", SECRET)
    # Cloudinary dummy: create_app() exige credenciales aunque las pruebas no suban archivos
    monkeypatch.setattr(Config, "CLOUDINARY_CLOUD_NAME", "demo")
    monkeypatch.setattr(Config, "CLOUDINARY_API_KEY", "123456")
    monkeypatch.setattr(Config, "CLOUDINARY_API_SECRET", "secreto-de-prueba")
    app = create_app()
    app.config.update({"TESTING": True, "SECRET_KEY": SECRET})

    with app.app_context():
        assert str(db.engine.url).startswith("sqlite"), "Las pruebas no deben tocar MySQL"
        db.create_all()

        db.session.add_all([
            Roles(idRol=1, nombre="Administrador"),
            Roles(idRol=2, nombre="Cliente"),
            Roles(idRol=3, nombre="Empleado"),
        ])
        db.session.commit()

        db.session.add(Categoria(idCategoria=1, nombre="Vestidos"))
        db.session.commit()

        db.session.add(Prenda(idPrenda=1, idCategoria=1, nombre_prenda="Vestido azul",
                              color="Azul", precio_alquiler=120000))
        db.session.commit()

        db.session.add_all([
            Inventario(idInventario=1, idPrenda=1, codigo_interno="VES-001", talla="M", estado="Disponible"),
            Inventario(idInventario=2, idPrenda=1, codigo_interno="VES-002", talla="L", estado="Reservado"),
        ])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()