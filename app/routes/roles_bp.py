from flask import Blueprint, request
from app.database.database import db
from app.models.roles import Roles
from app.utils.response import response_success, response_error, serialize_model, serialize_models
from app.utils.auth_middleware import admin_required

roles_bp = Blueprint('roles', __name__, url_prefix='/api/roles')

# GET - Obtener todos los roles
@roles_bp.route('', methods=['GET'])
def get_roles():
    try:
        roles = Roles.query.all()
        return response_success(serialize_models(roles), "Roles obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener rol por ID
@roles_bp.route('/<int:id>', methods=['GET'])
def get_rol(id):
    try:
        rol = Roles.query.get(id)
        if not rol:
            return response_error("Rol no encontrado", 404)
        return response_success(serialize_model(rol), "Rol obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear nuevo rol
@roles_bp.route('', methods=['POST'])
@admin_required
def create_rol():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        if 'nombre' not in data:
            return response_error("El campo 'nombre' es requerido", 400)
        
        # Verificar si el rol ya existe
        if Roles.query.filter_by(nombre=data['nombre']).first():
            return response_error("El rol ya existe", 400)
        
        rol = Roles(nombre=data['nombre'])
        rol.save()
        
        return response_success(serialize_model(rol), "Rol creado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar rol
@roles_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_rol(id):
    try:
        rol = Roles.query.get(id)
        if not rol:
            return response_error("Rol no encontrado", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        if 'nombre' in data:
            # Verificar que no exista otro rol con el mismo nombre
            existing = Roles.query.filter_by(nombre=data['nombre']).first()
            if existing and existing.idRol != id:
                return response_error("El rol ya existe", 400)
            rol.nombre = data['nombre']
        
        rol.save()
        
        return response_success(serialize_model(rol), "Rol actualizado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# DELETE - Eliminar rol
@roles_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_rol(id):
    try:
        rol = Roles.query.get(id)
        if not rol:
            return response_error("Rol no encontrado", 404)
        
        rol.delete()
        
        return response_success(message="Rol eliminado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
