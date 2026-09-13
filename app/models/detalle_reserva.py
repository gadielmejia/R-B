from app.database.database import db

class Detalle_Reserva(db.Model):
    __tablename__ = 'Detalle_Reserva'
    
    idDetalle_Reserva = db.Column(db.Integer, primary_key=True, autoincrement=True)

    idReserva = db.Column(db.Integer, db.ForeignKey('Reserva.idReserva'), nullable=False)

    idInventario = db.Column(db.Integer, db.ForeignKey('Inventario.idInventario'), nullable=False)

    cantidad = db.Column(db.Integer, default=1, nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
                
    reserva = db.relationship('Reserva', back_populates='detalles_reserva')
    
    inventario = db.relationship('Inventario', back_populates='detalles_reserva')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def __repr__(self):
        return f'<Detalle_Reserva {self.idDetalle_Reserva}>'
