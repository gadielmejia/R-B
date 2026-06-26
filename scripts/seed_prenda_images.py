import os
import shutil
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from app import create_app
from app.database.database import db
from app.models.prenda_imagen import PrendaImagen
from app.models.prenda import Prenda

FRONTEND_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'RENTSTYLE-FRONT-EDN', 'src', 'assets'))
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'uploads', 'prendas'))

PRODUCT_IMAGE_MAP = {
    1: 'vestidoverde.jpg',
    2: 'vestidonregro.jpg',
    3: 'vestidoazul.png',
    4: 'vestidorojo.png',
    5: 'vestidodorado.png',
}


def ensure_uploads_dir():
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def copy_asset_to_uploads(asset_name):
    src = os.path.join(FRONTEND_ASSETS_DIR, asset_name)
    if not os.path.isfile(src):
        raise FileNotFoundError(f"No se encontró el asset de imagen: {src}")
    dst_name = f"{os.path.splitext(asset_name)[0]}_{os.path.getmtime(src):.0f}{os.path.splitext(asset_name)[1]}"
    dst = os.path.join(UPLOADS_DIR, dst_name)
    shutil.copy2(src, dst)
    return dst_name


def main():
    ensure_uploads_dir()
    app = create_app()
    with app.app_context():
        for prenda_id, asset_name in PRODUCT_IMAGE_MAP.items():
            prenda = Prenda.query.get(prenda_id)
            if not prenda:
                print(f"[SKIP] Prenda {prenda_id} no encontrada")
                continue

            if prenda.imagenes:
                print(f"[SKIP] Prenda {prenda_id} ya tiene {len(prenda.imagenes)} imagen(es)")
                continue

            try:
                saved_filename = copy_asset_to_uploads(asset_name)
            except FileNotFoundError as exc:
                print(f"[ERROR] {exc}")
                continue

            imagen = PrendaImagen(idPrenda=prenda_id, filename=saved_filename)
            db.session.add(imagen)
            db.session.commit()
            print(f"[OK] Prenda {prenda_id} -> {saved_filename}")

        print("Seed terminado.")


if __name__ == '__main__':
    main()
