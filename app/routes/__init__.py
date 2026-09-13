                               
from app.routes.home_bp import home_bp
from app.routes.roles_bp import roles_bp
from app.routes.usuarios_bp import usuarios_bp
from app.routes.prendas_bp import prendas_bp
from app.routes.reservas_bp import reservas_bp
from app.routes.categorias_bp import categorias_bp
from app.routes.inventario_bp import inventario_bp

__all__ = [
    'home_bp',
    'roles_bp',
    'usuarios_bp',
    'prendas_bp',
    'reservas_bp',
    'categorias_bp',
    'inventario_bp'
]
