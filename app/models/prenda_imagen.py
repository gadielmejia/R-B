from app.database.database import db
from datetime import datetime

class PrendaImagen(db.Model):
    __tablename__ = 'PrendaImagen'

    idImagen = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idPrenda = db.Column(db.Integer, db.ForeignKey('Prenda.idPrenda'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prenda = db.relationship('Prenda', back_populates='imagenes')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<PrendaImagen {self.filename}>"
