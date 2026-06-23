from app import create_app
from app.config.settings import Config
from app.models.roles import Roles
from app.models.usuarios import Usuarios

app = create_app()

with app.app_context():
    print('SQLALCHEMY_DATABASE_URI =', Config.SQLALCHEMY_DATABASE_URI)
    print('\nRoles:')
    for r in Roles.query.order_by(Roles.idRol).all():
        print(f' - {r.idRol}: {r.nombre}')

    print('\nUsuarios (first 20):')
    users = Usuarios.query.limit(20).all()
    print(f' Count: {len(users)}')
    for u in users:
        print(f' - {u.idUsuario}: {u.nombre} <{u.correo}> doc={u.documento}')
