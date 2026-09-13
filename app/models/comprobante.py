from app.database.database import db
from datetime import datetime

class Comprobante(db.Model):
    __tablename__ = 'Comprobante'
    
    idComprobante = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idReserva = db.Column(db.Integer, db.ForeignKey('Reserva.idReserva'), nullable=False)
    numero_comprobante = db.Column(db.String(30), nullable=False, unique=True)
    tipo_comprobante = db.Column(db.Enum('Ticket', 'Factura', 'Recibo'), default='Ticket')
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.Enum('Pendiente', 'Emitido', 'Anulado'), default='Emitido')
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
                
    reserva = db.relationship('Reserva', back_populates='comprobante')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Comprobante {self.numero_comprobante}>'
