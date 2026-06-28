import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from app import create_app
from app.database.database import db
from app.models.prenda_imagen import PrendaImagen
from app.models.prenda import Prenda
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

FRONTEND_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'RENTSTYLE-FRONT-EDN', 'src', 'assets'))

PRODUCT_IMAGE_MAP = {
    1: 'vestidoverde.jpg',
    2: 'vestidonregro.jpg',
    3: 'vestidoazul.png',
    4: 'vestidorojo.png',
    5: 'vestidodorado.png',
}


def upload_to_cloudinary(asset_path, public_id):
    upload_result = cloudinary.uploader.upload(
        asset_path,
        public_id=public_id,
        folder=os.getenv('CLOUDINARY_UPLOAD_FOLDER', 'RentStyle/prendas'),
        overwrite=True,
        resource_type='image',
        format='auto',
        quality='auto',
    )
    return upload_result.get('public_id')


def main():
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

            src = os.path.join(FRONTEND_ASSETS_DIR, asset_name)
            if not os.path.isfile(src):
                print(f"[ERROR] No se encontró el asset de imagen: {src}")
                continue

            public_id = f"{os.getenv('CLOUDINARY_UPLOAD_FOLDER', 'RentStyle/prendas')}/{os.path.splitext(asset_name)[0]}"
            uploaded_public_id = upload_to_cloudinary(src, public_id)
            imagen = PrendaImagen(idPrenda=prenda_id, filename=uploaded_public_id)
            db.session.add(imagen)
            db.session.commit()
            print(f"[OK] Prenda {prenda_id} -> {uploaded_public_id}")

        print("Seed Cloudinary terminado.")


if __name__ == '__main__':
    main()
