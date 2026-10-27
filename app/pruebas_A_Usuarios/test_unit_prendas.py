import pytest
import jwt
from app.database.database import db
from app.models.categoria import Categoria
from app.models.prenda import Prenda
from app.models.inventario import Inventario
from app.models.lote import Lote
from app.routes.prendas_bp import _stock_summary


def _admin_token(app):
    return jwt.encode({"idUsuario": 1, "rol": "admin"}, app.config["SECRET_KEY"], algorithm="HS256")


def _client_token(app):
    return jwt.encode({"idUsuario": 2, "rol": "user"}, app.config["SECRET_KEY"], algorithm="HS256")


def test_unit01_crear_prenda_exitoso(client, app):
    with app.app_context():
        cat = Categoria(nombre="Vestidos")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.idCategoria

    token = _admin_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "nombre_prenda": "Vestido Elegante",
        "descripcion": "Vestido de noche largo",
        "precio_alquiler": 150.00,
        "idCategoria": cat_id
    }
    response = client.post("/api/prendas", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["data"]["nombre_prenda"] == "Vestido Elegante"


def test_unit02_crear_prenda_campos_faltantes(client, app):
    token = _admin_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "descripcion": "Sin nombre",
        "precio_alquiler": 100.00
    }
    response = client.post("/api/prendas", json=payload, headers=headers)
    assert response.status_code == 400


def test_unit03_obtener_detalle_prenda_inexistente(client):
    response = client.get("/api/prendas/99999")
    assert response.status_code == 404
    assert "Prenda no encontrada" in response.get_json()["message"]


def test_unit04_actualizar_prenda(client, app):
    with app.app_context():
        cat = Categoria(nombre="Trajes")
        db.session.add(cat)
        db.session.commit()
        prenda = Prenda(nombre_prenda="Traje Sastre", descripcion="Formal", precio_alquiler=200.0, idCategoria=cat.idCategoria)
        db.session.add(prenda)
        db.session.commit()
        prenda_id = prenda.idPrenda

    token = _admin_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(f"/api/prendas/{prenda_id}", json={"precio_alquiler": 250.0}, headers=headers)
    assert response.status_code == 200
    assert float(response.get_json()["data"]["precio_alquiler"]) == 250.0


def test_unit05_eliminar_prenda(client, app):
    with app.app_context():
        cat = Categoria(nombre="Accesorios")
        db.session.add(cat)
        db.session.commit()
        prenda = Prenda(nombre_prenda="Bolso", descripcion="De mano", precio_alquiler=50.0, idCategoria=cat.idCategoria)
        db.session.add(prenda)
        db.session.commit()
        prenda_id = prenda.idPrenda

    token = _admin_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete(f"/api/prendas/{prenda_id}", headers=headers)
    assert response.status_code == 200

    res_get = client.get(f"/api/prendas/{prenda_id}")
    assert res_get.status_code == 404


def test_unit06_stock_summary_calculo(app):
    with app.app_context():
        cat = Categoria(nombre="Prueba Stock")
        db.session.add(cat)
        db.session.commit()
        prenda = Prenda(nombre_prenda="Prenda Stock", descripcion="Test", precio_alquiler=100.0, idCategoria=cat.idCategoria)
        db.session.add(prenda)
        db.session.commit()

        inv1 = Inventario(idPrenda=prenda.idPrenda, codigo_interno="INV-001", estado="Disponible")
        inv2 = Inventario(idPrenda=prenda.idPrenda, codigo_interno="INV-002", estado="Alquilado")
        inv3 = Inventario(idPrenda=prenda.idPrenda, codigo_interno="INV-003", estado="Disponible")
        db.session.add_all([inv1, inv2, inv3])
        db.session.commit()

        summary = _stock_summary(prenda)
        assert summary["stock_total"] == 3
        assert summary["stock_disponible"] == 2
        assert summary["stock_alquilado"] == 1


def test_unit07_filtrar_prendas_por_categorias(client, app):
    with app.app_context():
        cat1 = Categoria(nombre="Cat A")
        cat2 = Categoria(nombre="Cat B")
        db.session.add_all([cat1, cat2])
        db.session.commit()

        p1 = Prenda(nombre_prenda="P1", descripcion="Desc", precio_alquiler=10.0, idCategoria=cat1.idCategoria)
        p2 = Prenda(nombre_prenda="P2", descripcion="Desc", precio_alquiler=20.0, idCategoria=cat2.idCategoria)
        db.session.add_all([p1, p2])
        db.session.commit()
        cat1_id = cat1.idCategoria

    response = client.get(f"/api/prendas/categoria/{cat1_id}")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["nombre_prenda"] == "P1"


def test_unit08_reporte_exige_admin(client):
    response = client.get("/api/reportes/trimestral/excel?year=2026&quarter=1")
    assert response.status_code in (401, 403)


def test_unit09_crear_lote_prendas(client, app):
    with app.app_context():
        cat = Categoria(nombre="Cat Lotes")
        db.session.add(cat)
        db.session.commit()
        prenda = Prenda(nombre_prenda="Prenda Lote", descripcion="Desc", precio_alquiler=50.0, idCategoria=cat.idCategoria)
        db.session.add(prenda)
        db.session.commit()
        prenda_id = prenda.idPrenda

    token = _admin_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "idPrenda": int(prenda_id),
        "nombre_lote": "Lote Verano 2026",
        "descripcion_lote": "Lote inicial de temporada",
        "cantidad_prendas": 15
    }
    response = client.post("/api/lotes", json=payload, headers=headers)
    assert response.status_code in (201, 200)
    data = response.get_json()
    assert data.get("success") is True or "data" in data


def test_unit10_serialize_prenda_imagenes(client, app):
    with app.app_context():
        cat = Categoria(nombre="Zapatos")
        db.session.add(cat)
        db.session.commit()
        prenda = Prenda(nombre_prenda="Zapato Tacón", descripcion="Elegante", precio_alquiler=80.0, idCategoria=cat.idCategoria)
        db.session.add(prenda)
        db.session.commit()
        prenda_id = prenda.idPrenda

    response = client.get(f"/api/prendas/{prenda_id}")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert "images" in data
    assert "stock" in data
    assert isinstance(data["images"], list)
