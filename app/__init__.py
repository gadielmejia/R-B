from flask import Flask
from flask_migrate import Migrate
<<<<<<< HEAD
from flask_cors import CORS
=======
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
from app.config.settings import Config
from app.database.database import db

def create_app():
    app = Flask(__name__)
<<<<<<< HEAD
    app.config.from_object(Config)
    db.init_app(app)
    CORS(app, origins=["http://localhost:5173"])
    migrate = Migrate(app, db)

=======
    
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Inicializar Migrate después de db.init_app
    migrate = Migrate(app, db)
    
    # Importar todos los modelos para que SQLAlchemy los reconozca
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
    from app.models import (
        Roles, Categoria, Usuarios, Prenda, Inventario,
        Reserva, Detalle_Reserva, Comprobante, Cita
    )
<<<<<<< HEAD

=======
    
    # Registrar Blueprints
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
    from app.routes.home_bp import home_bp
    from app.routes.roles_bp import roles_bp
    from app.routes.usuarios_bp import usuarios_bp
    from app.routes.prendas_bp import prendas_bp
    from app.routes.reservas_bp import reservas_bp
    from app.routes.categorias_bp import categorias_bp
    from app.routes.inventario_bp import inventario_bp
<<<<<<< HEAD
    from app.routes.auth_bp import auth_bp

=======
    
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
    app.register_blueprint(home_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(prendas_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(inventario_bp)
<<<<<<< HEAD
    app.register_blueprint(auth_bp)

    return app
=======
    
    return app
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
