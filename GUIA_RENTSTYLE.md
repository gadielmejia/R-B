# 🚀 Guía para conectar RentStyle Frontend + Backend

## Estructura del proyecto

```
rentstyle/
├── backend/   ← RENTSTYLE-BACK-END-main
└── frontend/  ← RENTSTYLE-FRONT-EDN-main
```

---

## 1. REQUISITOS PREVIOS

- Python 3.10+
- Node.js 18+
- MySQL instalado y corriendo
- pip

---

## 2. CONFIGURAR EL BACKEND (Flask)

### 2.1 Crea la base de datos en MySQL

```sql
CREATE DATABASE rentstyle CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 Crea el archivo `.env`

Dentro de `RENTSTYLE-BACK-END-main/`, crea un archivo `.env` (copia de `.env.example`):

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=TU_CONTRASEÑA_MYSQL
MYSQL_DATABASE=rentstyle
SECRET_KEY=una_clave_secreta_cualquiera_123
```

### 2.3 Instala dependencias

```bash
cd RENTSTYLE-BACK-END-main
pip install -r requirements.txt 
```

> ⚠️ Si falla `mysqlclient`, en Windows instala primero:  
> `pip install mysqlclient` requiere compiladores. Alternativa: ya está `PyMySQL` en requirements, que es puro Python.

### 2.4 Migra la base de datos

```bash
flask db init      # Solo la primera vez
flask db migrate -m "initial"
flask db upgrade
```

> Si `flask` no se reconoce: `python -m flask db init`

### 2.5 Corre el backend

```bash
python run.py
```

El backend quedará en: **http://localhost:5000**

Puedes verificar abriendo: http://localhost:5000/ → debe responder JSON con los endpoints disponibles.

---

## 3. CONFIGURAR EL FRONTEND (React + Vite)

### 3.1 Instala dependencias

```bash
cd RENTSTYLE-FRONT-EDN-main
npm install
```

### 3.2 Crea el archivo `.env` del frontend

Dentro de `RENTSTYLE-FRONT-EDN-main/`, crea `.env`:

```env
VITE_API_URL=http://localhost:5000
```

### 3.3 Actualiza `vite.config.js` (proxy para evitar CORS en desarrollo)

Reemplaza el contenido de `vite.config.js` con:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
```

### 3.4 Corre el frontend

```bash
npm run dev
```

El frontend quedará en: **http://localhost:5173**

---

## 4. MODIFICACIONES AL CÓDIGO

### 4.1 Backend — Habilitar CORS correctamente

El backend ya tiene `flask-cors` instalado. Modifica `app/__init__.py` para habilitarlo:

```python
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS                          # ← AGREGA
from app.config.settings import Config
from app.database.database import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    CORS(app, origins=["http://localhost:5173"])      # ← AGREGA

    migrate = Migrate(app, db)

    from app.models import (
        Roles, Categoria, Usuarios, Prenda, Inventario,
        Reserva, Detalle_Reserva, Comprobante, Cita
    )

    from app.routes.home_bp import home_bp
    from app.routes.roles_bp import roles_bp
    from app.routes.usuarios_bp import usuarios_bp
    from app.routes.prendas_bp import prendas_bp
    from app.routes.reservas_bp import reservas_bp
    from app.routes.categorias_bp import categorias_bp
    from app.routes.inventario_bp import inventario_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(prendas_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(inventario_bp)

    return app
```

### 4.2 Backend — Agregar endpoint de login

El backend no tiene ruta `/api/login`. Crea el archivo `app/routes/auth_bp.py`:

```python
from flask import Blueprint, request
from app.database.database import db
from app.models.usuarios import Usuarios
from app.utils.response import response_success, response_error, serialize_model

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'correo' not in data or 'Contrasena' not in data:
            return response_error("Correo y contraseña son requeridos", 400)

        usuario = Usuarios.query.filter_by(correo=data['correo']).first()
        if not usuario or usuario.Contrasena != data['Contrasena']:
            return response_error("Correo o contraseña incorrectos", 401)

        user_data = serialize_model(usuario)
        user_data['rol_nombre'] = usuario.rol.nombre if usuario.rol else None

        return response_success(user_data, "Login exitoso")
    except Exception as e:
        return response_error(str(e), 500)
```

Luego regístralo en `app/__init__.py`, añadiendo estas dos líneas justo antes del `return app`:

```python
from app.routes.auth_bp import auth_bp
app.register_blueprint(auth_bp)
```

### 4.3 Backend — Agregar campo `nombre` al modelo Roles

Para que `usuario.rol.nombre` funcione en el login, verifica que `app/models/roles.py` tenga un campo `nombre`. Si no lo tiene, agrégalo:

```python
class Roles(db.Model):
    __tablename__ = 'Roles'
    idRol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)   # ← verifica que exista
    usuarios = db.relationship('Usuarios', back_populates='rol')
```

### 4.4 Frontend — Conectar el Login con el API

Reemplaza la función `handleSubmit` en `src/pages/Login.jsx` para que use el backend:

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo: email, Contrasena: password }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.message || 'Credenciales incorrectas');
      return;
    }
    localStorage.setItem('currentUser', JSON.stringify(data.data));
    if (data.data.rol_nombre === 'admin') {
      window.location.href = '/dashboardadmin';
    } else {
      window.location.href = '/dashboarduser';
    }
  } catch (err) {
    alert('Error de conexión con el servidor');
  }
};
```

Y elimina el array `users` hardcodeado que ya no se necesita.

### 4.5 Frontend — Conectar el Registro con el API

El formulario de registro (`register.jsx`) actualmente no hace POST al backend. Busca donde se maneja el submit del formulario y agrega:

```js
const res = await fetch('/api/usuarios', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nombre: formData.name,
    correo: formData.email,
    Contrasena: hashedPassword,   // ya lo hashea con crypto.subtle
    documento: formData.documento || '000000',  // ajusta según tu form
    idRol: 2,  // 2 = usuario normal (debes insertar los roles primero)
  }),
});
```

---

## 5. DATOS INICIALES (Roles en la BD)

Después de correr las migraciones, inserta los roles base:

```sql
USE rentstyle;
INSERT INTO Roles (nombre) VALUES ('admin'), ('usuario');
```

---

## 6. FLUJO COMPLETO DE PRUEBA

1. Arranca MySQL
2. Corre el backend: `python run.py` → http://localhost:5000
3. Corre el frontend: `npm run dev` → http://localhost:5173
4. Ve a http://localhost:5173/registro y crea un usuario
5. Ve a http://localhost:5173/login e inicia sesión
6. Verifica en http://localhost:5000/api/usuarios que el usuario aparece

---

## 7. RESUMEN DE CAMBIOS NECESARIOS

| Archivo | Cambio |
|---|---|
| `backend/app/__init__.py` | Agregar `CORS(app, ...)` e importar `auth_bp` |
| `backend/app/routes/auth_bp.py` | **CREAR** — endpoint `/api/login` |
| `backend/.env` | **CREAR** — credenciales de MySQL |
| `frontend/vite.config.js` | Agregar proxy a `http://localhost:5000` |
| `frontend/.env` | **CREAR** — `VITE_API_URL=http://localhost:5000` |
| `frontend/src/pages/Login.jsx` | Reemplazar login hardcodeado por fetch al API |
| BD MySQL | Crear base de datos e insertar roles iniciales |
