from app.database.database import db
from datetime import datetime

class Lote(db.Model):
    __tablename__ = 'Lote'

    idLote = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idPrenda = db.Column(db.Integer, db.ForeignKey('Prenda.idPrenda'), nullable=False)
    nombre_lote = db.Column(db.String(100), nullable=False)
    descripcion_lote = db.Column(db.Text, nullable=True)
    cantidad_prendas = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prenda = db.relationship('Prenda', back_populates='lotes')
    inventarios = db.relationship('Inventario', back_populates='lote', cascade='all, delete-orphan')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<Lote {self.nombre_lote}>'
