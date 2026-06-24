from flask import Blueprint, request
from app.database.database import db
from app.models.usuarios import Usuarios
from app.models.roles import Roles
from app.utils.response import response_success, response_error, serialize_model, serialize_models

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

# GET - Obtener todos los usuarios
@usuarios_bp.route('', methods=['GET'])
def get_usuarios():
    try:
        usuarios = Usuarios.query.all()
        return response_success(serialize_models(usuarios), "Usuarios obtenidos exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# GET - Obtener usuario por ID
@usuarios_bp.route('/<int:id>', methods=['GET'])
def get_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)
        return response_success(serialize_model(usuario), "Usuario obtenido exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# POST - Crear nuevo usuario
@usuarios_bp.route('', methods=['POST'])
def create_usuario():
    try:
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Validar campos requeridos
        required_fields = ['nombre', 'documento', 'correo', 'Contrasena']
        for field in required_fields:
            if field not in data:
                return response_error(f"El campo '{field}' es requerido", 400)
        
        # Verificar si el usuario ya existe
        if Usuarios.query.filter_by(documento=data['documento']).first():
            return response_error("El documento ya está registrado", 400)
        if Usuarios.query.filter_by(correo=data['correo']).first():
            return response_error("El correo ya está registrado", 400)
        
        # Asignar automáticamente el rol de cliente si no se proporciona
        id_rol = data.get('idRol')
        if not id_rol:
            # Buscar el rol "Cliente"
            rol_cliente = Roles.query.filter(Roles.nombre.ilike('cliente')).first()
            if not rol_cliente:
                return response_error("El rol 'Cliente' no existe en el sistema", 500)
            id_rol = rol_cliente.idRol
        else:
            # Verificar que el rol existe si se proporciona
            if not Roles.query.get(id_rol):
                return response_error("El rol especificado no existe", 400)
        
        usuario = Usuarios(
            nombre=data['nombre'],
            documento=data['documento'],
            correo=data['correo'],
            Contrasena=data['Contrasena'],
            idRol=id_rol,
            telefono=data.get('telefono')
        )
        usuario.save()
        
        return response_success(serialize_model(usuario), "Usuario creado exitosamente", 201)
    except Exception as e:
        return response_error(str(e), 500)

# PUT - Actualizar usuario
@usuarios_bp.route('/<int:id>', methods=['PUT'])
def update_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)
        
        data = request.get_json()
        
        if not data:
            return response_error("El body debe ser un JSON válido", 400)
        
        # Actualizar solo los campos proporcionados
        if 'nombre' in data:
            usuario.nombre = data['nombre']
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        if 'Contrasena' in data:
            usuario.Contrasena = data['Contrasena']
        if 'idRol' in data:
            if not Roles.query.get(data['idRol']):
                return response_error("El rol especificado no existe", 400)
            usuario.idRol = data['idRol']
        
        usuario.save()
        
        return response_success(serialize_model(usuario), "Usuario actualizado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)

# DELETE - Eliminar usuario
@usuarios_bp.route('/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    try:
        usuario = Usuarios.query.get(id)
        if not usuario:
            return response_error("Usuario no encontrado", 404)
        
        usuario.delete()
        
        return response_success(message="Usuario eliminado exitosamente")
    except Exception as e:
        return response_error(str(e), 500)
