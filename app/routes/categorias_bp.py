from flask import Blueprint, request
from app.database.database import db
from app.models.categoria import Categoria
from app.utils.auth_middleware import token_required
from app.utils.response import response_success, response_error, serialize_model, serialize_models

categorias_bp = Blueprint('categorias', __name__, url_prefix='/api/categorias')

                                    
@categorias_bp.route('', methods=['GET'])
def get_categorias():
    try:
        categorias = Categoria.query.all()
        return response_success(serialize_models(categorias), "Categorías obtenidas exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                                
@categorias_bp.route('/<int:id>', methods=['GET'])
def get_categoria(id):
    try:
        categoria = Categoria.query.get(id)
        if not categoria:
            return response_error("Categoría no encontrada", 404)
        return response_success(serialize_model(categoria), "Categoría obtenida exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                              
@categorias_bp.route('', methods=['POST'])
@token_required
def create_categoria():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        if 'nombre' not in data:
            return response_error("El campo 'nombre' es requerido", 400)
        
                                             
        if Categoria.query.filter_by(nombre=data['nombre']).first():
            return response_error("La categoría ya existe", 400)
        
        categoria = Categoria(nombre=data['nombre'])
        categoria.save()
        
        return response_success(serialize_model(categoria), "Categoría creada exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

                            
@categorias_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_categoria(id):
    try:
        categoria = Categoria.query.get(id)
        if not categoria:
            return response_error("Categoría no encontrada", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        if 'nombre' in data:
                                                                        
            existing = Categoria.query.filter_by(nombre=data['nombre']).first()
            if existing and existing.idCategoria != id:
                return response_error("La categoría ya existe", 400)
            categoria.nombre = data['nombre']
        
        categoria.save()
        
        return response_success(serialize_model(categoria), "Categoría actualizada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

                             
@categorias_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_categoria(id):
    try:
        categoria = Categoria.query.get(id)
        if not categoria:
            return response_error("Categoría no encontrada", 404)
        
        categoria.delete()
        
        return response_success(message="Categoría eliminada exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
