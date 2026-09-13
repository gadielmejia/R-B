from app.database.database import db

class Roles(db.Model):
    __tablename__ = 'Roles'
    
    idRol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(30), nullable=False, unique=True)
    
                
    usuarios = db.relationship('Usuarios', back_populates='rol')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Roles {self.nombre}>'
