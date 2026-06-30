from app.database.database import db
from datetime import datetime

class Inventario(db.Model):
    __tablename__ = 'Inventario'
    
    idInventario = db.Column(db.Integer, primary_key=True, autoincrement=True)

    idPrenda = db.Column(db.Integer, db.ForeignKey('Prenda.idPrenda'), nullable=False)
    idLote = db.Column(db.Integer, db.ForeignKey('Lote.idLote'), nullable=True)

    codigo_interno = db.Column(db.String(30), nullable=False, unique=True)

    talla = db.Column(db.String(10), nullable=True)

    estado = db.Column(db.Enum('Disponible', 'Reservado', 'Alquilado', 'Reparacion'), default='Disponible')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    prenda = db.relationship('Prenda', back_populates='inventarios')
    lote = db.relationship('Lote', back_populates='inventarios')
    detalles_reserva = db.relationship('Detalle_Reserva', back_populates='inventario')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def __repr__(self):
        return f'<Inventario {self.codigo_interno}>'
