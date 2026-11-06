import pytest

from app.database.database import db
from app.models.prenda import Prenda
from app.models.inventario import Inventario


# INT-PRENDA-01: creación de prenda vía HTTP + persistencia en BD.
def test_integracion_crear_prenda(client, app):
    payload = {
        "nombre_prenda": "Vestido rojo",
        "idCategoria": 1,
        "precio_alquiler": 150000,
        "color": "Rojo",
        "descripcion": "Vestido de prueba de integracion",
        "inventory_codes": ["PRE-001", "PRE-002"],
    }

    response = client.post("/api/prendas", json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["nombre_prenda"] == "Vestido rojo"

    with app.app_context():
        saved = Prenda.query.filter_by(nombre_prenda="Vestido rojo").first()
        assert saved is not None
        assert saved.idCategoria == 1
        assert float(saved.precio_alquiler) == 150000.0

        inventarios = Inventario.query.filter_by(idPrenda=saved.idPrenda).all()
        assert len(inventarios) == 2
        codigos = {inv.codigo_interno for inv in inventarios}
        assert codigos == {"PRE-001", "PRE-002"}


# INT-PRENDA-02: edición de prenda vía HTTP + persistencia en BD.
def test_integracion_editar_prenda(client, app):
    payload = {
        "nombre_prenda": "Vestido azul editado",
        "precio_alquiler": 135000,
        "color": "Azul marino",
        "descripcion": "Descripcion editada",
    }

    response = client.put("/api/prendas/1", json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["nombre_prenda"] == "Vestido azul editado"

    with app.app_context():
        saved = db.session.get(Prenda, 1)
        assert saved is not None
        assert saved.nombre_prenda == "Vestido azul editado"
        assert float(saved.precio_alquiler) == 135000.0
        assert saved.color == "Azul marino"
        assert saved.descripcion == "Descripcion editada"


# INT-PRENDA-03 (propuesta): eliminación de prenda vía HTTP + verificación de persistencia.
def test_integracion_eliminar_prenda(client, app):
    response = client.delete("/api/prendas/1")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "success"

    with app.app_context():
        assert db.session.get(Prenda, 1) is None
        assert Inventario.query.filter_by(idPrenda=1).count() == 0

    # Tras eliminar, la consulta por ID debe responder 404.
    get_response = client.get("/api/prendas/1")
    assert get_response.status_code == 404


# INT-PRENDA-04 (propuesta): consulta de prenda por ID + verificación de stock resumido.
def test_integracion_obtener_prenda_por_id(client, app):
    response = client.get("/api/prendas/1")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "success"
    data = body["data"]

    assert data["idPrenda"] == 1
    assert data["nombre_prenda"] == "Vestido azul"
    assert "stock" in data
    assert data["stock"]["stock_total"] == 2
    assert data["stock"]["stock_disponible"] == 1
    assert data["stock"]["stock_reservado"] == 1