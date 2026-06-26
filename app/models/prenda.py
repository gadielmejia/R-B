from app.database.database import db
from datetime import datetime

class Prenda(db.Model):
    __tablename__ = 'Prenda'
    
    idPrenda = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idCategoria = db.Column(db.Integer, db.ForeignKey('Categoria.idCategoria'), nullable=False)
    nombre_prenda = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    talla = db.Column(db.String(10))
    color = db.Column(db.String(30))
    precio_alquiler = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    categoria = db.relationship('Categoria', back_populates='prendas')
    inventarios = db.relationship('Inventario', back_populates='prenda')
    # Imágenes relacionadas
    imagenes = db.relationship('PrendaImagen', back_populates='prenda', cascade='all, delete-orphan')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Prenda {self.nombre_prenda}>'
