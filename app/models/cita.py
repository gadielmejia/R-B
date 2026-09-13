from app.database.database import db
from datetime import datetime

class Cita(db.Model):
    __tablename__ = 'Cita'
    
    idCita = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_administrador = db.Column(db.Integer, db.ForeignKey('Usuarios.idUsuario'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('Usuarios.idUsuario'), nullable=False)
    id_reserva = db.Column(db.Integer, db.ForeignKey('Reserva.idReserva'))
    fecha_cita = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(150))
    estado = db.Column(db.Enum('Pendiente', 'Atendida', 'Cancelada'), default='Pendiente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
                
    administrador = db.relationship('Usuarios', foreign_keys=[id_administrador], back_populates='citas_administrador')
    cliente = db.relationship('Usuarios', foreign_keys=[id_cliente], back_populates='citas_cliente')
    reserva = db.relationship('Reserva', back_populates='citas')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Cita {self.idCita}>'
