import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.models.prenda_imagen import PrendaImagen
import cloudinary
import cloudinary.api


def print_resources(folder=None):
    try:
        params = {'max_results': 100}
        if folder:
            params['prefix'] = folder.rstrip('/')
            params['type'] = 'upload'
        result = cloudinary.api.resources(**params)
        print(f"Resources in {folder or 'root'}:")
        for r in result.get('resources', []):
            print(' -', r.get('public_id'), r.get('format'), r.get('secure_url'))
        print(f"Total: {result.get('total_count')}")
    except Exception as e:
        print('Error listing resources:', e)


def print_folders(folder=None):
    try:
        params = {'max_results': 100}
        if folder:
            params['prefix'] = folder.rstrip('/')
        result = cloudinary.api.sub_folders(**params)
        print(f"Subfolders in {folder or 'root'}:")
        for f in result.get('folders', []):
            print(' -', f.get('path'))
    except Exception as e:
        print('Error listing folders:', e)


def main():
    print('CLOUDINARY_URL=', os.getenv('CLOUDINARY_URL'))
    print('CLOUDINARY_CLOUD_NAME=', os.getenv('CLOUDINARY_CLOUD_NAME'))
    print('CLOUDINARY_API_KEY=', os.getenv('CLOUDINARY_API_KEY'))
    print('CLOUDINARY_API_SECRET=', os.getenv('CLOUDINARY_API_SECRET'))

    print('cloudinary config:', cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret)
    print('\nListing folders...')
    print_folders('RentStyle')
    print('\nListing resources in RentStyle...')
    print_resources('RentStyle')
    print('\nListing resources in RentStyle/prendas...')
    print_resources('RentStyle/prendas')

    app = create_app()
    with app.app_context():
        print('\nDatabase Image Rows:')
        for img in PrendaImagen.query.order_by(PrendaImagen.idImagen).all():
            print(f'{img.idImagen}: prenda={img.idPrenda}, filename={img.filename}')

    upload_dir = ROOT_DIR / 'app' / 'static' / 'uploads' / 'prendas'
    print('\nLocal files:')
    for p in sorted(upload_dir.iterdir()):
        if p.is_file():
            print(' -', p.name)

if __name__ == '__main__':
    main()
