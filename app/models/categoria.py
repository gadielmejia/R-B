from app.database.database import db

class Categoria(db.Model):
    __tablename__ = 'Categoria'
    
    idCategoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    
                
    prendas = db.relationship('Prenda', back_populates='categoria')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'
