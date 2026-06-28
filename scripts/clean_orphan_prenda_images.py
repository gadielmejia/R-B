import os
from pathlib import Path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.database.database import db
from app.models.prenda import Prenda
from app.models.prenda_imagen import PrendaImagen
import cloudinary.uploader

UPLOAD_DIR = ROOT_DIR / 'app' / 'static' / 'uploads' / 'prendas'


def upload_local_image_to_cloudinary(filename):
    file_path = UPLOAD_DIR / filename
    public_id = f"{os.getenv('CLOUDINARY_UPLOAD_FOLDER', 'RentStyle/prendas')}/{Path(filename).stem}"
    result = cloudinary.uploader.upload(
        str(file_path),
        public_id=public_id,
        overwrite=True,
        resource_type='image',
        quality='auto',
    )
    return result.get('public_id')


def main():
    app = create_app()
    with app.app_context():
        prenda_ids = {p.idPrenda for p in Prenda.query.all()}
        image_rows = list(PrendaImagen.query.order_by(PrendaImagen.idImagen).all())

        print('--- DB prendas ---')
        for p in Prenda.query.order_by(Prenda.idPrenda).all():
            print(f'{p.idPrenda}: {p.nombre_prenda}')

        print('\n--- PrendaImagen rows ---')
        for img in image_rows:
            print(f'{img.idImagen}: prenda={img.idPrenda}, filename={img.filename}')

        print('\n--- Local files ---')
        local_files = sorted([f.name for f in UPLOAD_DIR.iterdir() if f.is_file()])
        for name in local_files:
            print(name)

        invalid_images = [img for img in image_rows if img.idPrenda not in prenda_ids]
        print('\n--- Invalid DB image rows (orphan prenda) ---')
        for img in invalid_images:
            print(f'{img.idImagen}: prenda={img.idPrenda}, filename={img.filename}')

        for img in invalid_images:
            path = UPLOAD_DIR / img.filename
            if path.exists():
                try:
                    path.unlink()
                    print(f'Deleted orphan local file: {img.filename}')
                except Exception as e:
                    print(f'Failed to delete orphan local file {img.filename}: {e}')
            db.session.delete(img)

        db.session.commit()

        print('\n--- Uploading valid local images to Cloudinary ---')
        updated = 0
        for img in PrendaImagen.query.order_by(PrendaImagen.idImagen).all():
            file_path = UPLOAD_DIR / img.filename
            if file_path.exists():
                try:
                    public_id = upload_local_image_to_cloudinary(img.filename)
                    img.filename = public_id
                    db.session.add(img)
                    file_path.unlink()
                    updated += 1
                    print(f'Uploaded and converted: {img.idImagen} -> {public_id}')
                except Exception as e:
                    print(f'Failed to upload {img.filename}: {e}')

        if updated:
            db.session.commit()

        print('\nCleanup and upload complete.')


if __name__ == '__main__':
    main()
