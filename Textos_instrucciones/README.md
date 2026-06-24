# RentStyle Backend API

Aplicación backend para el sistema de alquiler de prendas **RentStyle**, desarrollada con Flask y MySQL.

## 📋 Requisitos Previos

- Python 3.8+
- MySQL Server 5.7+
- Git

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd RENTSTYLE-BACK-END
```

### 2. Crear y activar el ambiente virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de MySQL:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña
MYSQL_DATABASE=rentstyle
SECRET_KEY=tu_clave_secreta
```

### 5. Crear la base de datos

```bash
CREATE DATABASE rentstyle CHARACTER SET utf8mb4;
```

### 6. Ejecutar migraciones

```bash
flask --app run db upgrade
```

## 🏃 Ejecutar el servidor

```bash
flask --app run run
```

El servidor estará disponible en `http://127.0.0.1:5000`

## 📚 Endpoints Disponibles

### Roles
- `GET /api/roles` - Obtener todos los roles
- `POST /api/roles` - Crear rol
- `GET /api/roles/<id>` - Obtener rol
- `PUT /api/roles/<id>` - Actualizar rol
- `DELETE /api/roles/<id>` - Eliminar rol

### Categorías
- `GET /api/categorias` - Obtener todas las categorías
- `POST /api/categorias` - Crear categoría
- `GET /api/categorias/<id>` - Obtener categoría
- `PUT /api/categorias/<id>` - Actualizar categoría
- `DELETE /api/categorias/<id>` - Eliminar categoría

### Usuarios
- `GET /api/usuarios` - Obtener todos los usuarios
- `POST /api/usuarios` - Crear usuario
- `GET /api/usuarios/<id>` - Obtener usuario
- `PUT /api/usuarios/<id>` - Actualizar usuario
- `DELETE /api/usuarios/<id>` - Eliminar usuario

### Prendas
- `GET /api/prendas` - Obtener todas las prendas
- `POST /api/prendas` - Crear prenda
- `GET /api/prendas/<id>` - Obtener prenda
- `PUT /api/prendas/<id>` - Actualizar prenda
- `DELETE /api/prendas/<id>` - Eliminar prenda

### Inventario
- `GET /api/inventario` - Obtener inventario
- `POST /api/inventario` - Agregar item
- `GET /api/inventario/<id>` - Obtener item
- `PUT /api/inventario/<id>` - Actualizar item
- `DELETE /api/inventario/<id>` - Eliminar item

### Reservas
- `GET /api/reservas` - Obtener todas las reservas
- `POST /api/reservas` - Crear reserva
- `GET /api/reservas/<id>` - Obtener reserva
- `PUT /api/reservas/<id>` - Actualizar reserva
- `DELETE /api/reservas/<id>` - Eliminar reserva

## 📁 Estructura del Proyecto

```
RENTSTYLE-BACK-END/
├── app/
│   ├── config/          # Configuración de la app
│   ├── database/        # Conexión a base de datos
│   ├── models/          # Modelos SQLAlchemy
│   ├── routes/          # Blueprints (endpoints)
│   ├── utils/           # Funciones auxiliares
│   └── __init__.py      # Inicialización de la app
├── migrations/          # Migraciones de base de datos
├── .env                 # Variables de entorno (no incluir en Git)
├── .env.example         # Plantilla de variables
├── .gitignore           # Archivos a ignorar en Git
├── requirements.txt     # Dependencias del proyecto
└── run.py              # Archivo principal para ejecutar
```

## 🔧 Tecnologías Utilizadas

- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM
- **Flask-Migrate** - Migraciones de base de datos
- **MySQL** - Base de datos
- **Python** - Lenguaje de programación

## 👥 Equipo

- Desarrollador Backend: [Tu Nombre]

## 📝 Notas Importantes

1. **Nunca subir `.env`** a Git - Solo `.env.example`
2. **Rama principal:** `main`
3. **Crear rama para cada feature:** `git checkout -b feature/nombre-feature`
4. **Hacer commit descriptivos:** `git commit -m "feat: descripción del cambio"`

## ❓ Problemas Comunes

### Error de conexión a MySQL
- Verifica que MySQL esté corriendo
- Comprueba las credenciales en `.env`

### Puerto 5000 en uso
```bash
lsof -i :5000  # En Linux/macOS
netstat -ano | findstr :5000  # En Windows
```

## 📞 Soporte

Para dudas o problemas, contacta con el equipo de desarrollo.
