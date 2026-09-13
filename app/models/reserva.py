from app.database.database import db
from datetime import datetime

class Reserva(db.Model):
    __tablename__ = 'Reserva'
    
    idReserva = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('Usuarios.idUsuario'), nullable=False)
    id_administrador = db.Column(db.Integer, db.ForeignKey('Usuarios.idUsuario'), nullable=False)
    fecha_reserva = db.Column(db.Date, nullable=False)
    fecha_evento = db.Column(db.Date, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date)
    estado = db.Column(db.Enum('Pendiente', 'Confirmada', 'Entregada', 'Finalizada', 'Cancelada'), default='Pendiente')
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
                
    cliente = db.relationship('Usuarios', foreign_keys=[id_cliente], back_populates='reservas_cliente')
    administrador = db.relationship('Usuarios', foreign_keys=[id_administrador], back_populates='reservas_administrador')
    detalles_reserva = db.relationship('Detalle_Reserva', back_populates='reserva')
    comprobante = db.relationship('Comprobante', back_populates='reserva')
    citas = db.relationship('Cita', back_populates='reserva')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Reserva {self.idReserva}>'
