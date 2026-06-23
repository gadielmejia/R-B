from app import create_app
from app.database.database import db
from app.models.roles import Roles

app = create_app()

with app.app_context():
    wanted = ['Administrador', 'Cliente']
    created = []
    for name in wanted:
        if not Roles.query.filter_by(nombre=name).first():
            r = Roles(nombre=name)
            db.session.add(r)
            created.append(name)
    if created:
        db.session.commit()
        print('Inserted roles:', created)
    else:
        print('All roles already exist:', [r.nombre for r in Roles.query.all()])
