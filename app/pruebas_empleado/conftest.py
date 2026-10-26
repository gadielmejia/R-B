from datetime import date, datetime, timedelta
 
import jwt
import pytest
from werkzeug.security import generate_password_hash
 
from app import create_app
from app.config.settings import Config
from app.database.database import db
from app.models.categoria import Categoria
from app.models.detalle_reserva import Detalle_Reserva
from app.models.inventario import Inventario
from app.models.prenda import Prenda
from app.models.reserva import Reserva
from app.models.roles import Roles
from app.models.usuarios import Usuarios
 
SECRET = "test-secret-key-rentstyle"
PASS_EMPLEADO = "Empleado123!"
 
 
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
 
        db.session.add_all([
            Usuarios(nombre="Admin Test", documento="1000000001", correo="admin@rentstyle.com",
                     Contrasena=generate_password_hash("admin123"), idRol=1),
            Usuarios(nombre="Juan Perez", documento="1020304050", correo="juan@test.com",
                     Contrasena=generate_password_hash("Test1234!"), idRol=2),
            Usuarios(nombre="Admin Secundario", documento="1000000004", correo="admin2@rentstyle.com",
                     Contrasena=generate_password_hash("admin456"), idRol=1),   # sin reservas asociadas
            Usuarios(nombre="Laura Gomez", documento="1000000003", correo="empleado@rentstyle.com",
                     Contrasena=generate_password_hash(PASS_EMPLEADO), idRol=3),
        ])
        db.session.commit()
 
        # Catálogo e inventario base
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
 
        # Reserva Pendiente del cliente Juan con la prenda VES-002 (Reservado)
        reserva = Reserva(id_cliente=2, id_administrador=1,
                          fecha_reserva=date(2026, 10, 20), fecha_evento=date(2026, 11, 5),
                          fecha_inicio=date(2026, 11, 4), fecha_fin=date(2026, 11, 7),
                          estado="Pendiente")
        db.session.add(reserva)
        db.session.commit()
        db.session.add(Detalle_Reserva(idReserva=reserva.idReserva, idInventario=2, cantidad=1, subtotal=120000))
        db.session.commit()
 
        yield app
        db.session.remove()
        db.drop_all()
 
 
@pytest.fixture
def client(app):
    return app.test_client()
 
 
def make_token(rol, id_usuario=3, correo="empleado@rentstyle.com", expira_en=timedelta(hours=1)):
    payload = {"idUsuario": id_usuario, "correo": correo, "rol": rol,
               "exp": datetime.utcnow() + expira_en}
    return jwt.encode(payload, SECRET, algorithm="HS256")
 
 
@pytest.fixture
def headers_empleado():
    """Cabecera Authorization de un empleado con sesión vigente."""
    return {"Authorization": "Bearer " + make_token("empleado")}