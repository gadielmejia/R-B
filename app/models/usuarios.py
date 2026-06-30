from app.database.database import db
from datetime import datetime

class Usuarios(db.Model):
    __tablename__ = 'Usuarios'
    
    idUsuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idRol = db.Column(db.Integer, db.ForeignKey('Roles.idRol'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), nullable=False, unique=True)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100), nullable=False, unique=True)
    avatar_url = db.Column(db.String(255))
    Contrasena = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    rol = db.relationship('Roles', back_populates='usuarios')
    reservas_cliente = db.relationship('Reserva', foreign_keys='Reserva.id_cliente', back_populates='cliente')
    reservas_administrador = db.relationship('Reserva', foreign_keys='Reserva.id_administrador', back_populates='administrador')
    citas_administrador = db.relationship('Cita', foreign_keys='Cita.id_administrador', back_populates='administrador')
    citas_cliente = db.relationship('Cita', foreign_keys='Cita.id_cliente', back_populates='cliente')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Usuarios {self.nombre}>'
