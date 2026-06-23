# 🌊 Git Flow - Flujo de Trabajo Avanzado

## ¿Qué es Git Flow?

Git Flow es un modelo de ramificación más robusto que Git simple. Define ramas específicas para:
- **main**: Código en producción
- **develop**: Rama de integración para desarrollo
- **feature/**: Nuevas características
- **release/**: Preparación para release
- **hotfix/**: Correcciones urgentes en producción

---

## 📦 Instalación de Git Flow

### Windows
```bash
# Descargar desde
# https://github.com/nvie/gitflow/wiki/Windows

# O instalar con Chocolatey
choco install git-flow
```

### Verificar instalación
```bash
git flow version
```

---

## 🚀 Inicializar Git Flow en el Proyecto

### Paso 1: Crear repositorio base
```bash
cd RENTSTYLE-BACK-END
git init
git add .
git commit -m "Initial commit: RentStyle backend"
```

### Paso 2: Crear rama develop
```bash
git checkout -b develop
<<<<<<< HEAD
git push -u origin develo
=======
git push -u origin develop
>>>>>>> 89f9ae44fcb446184234ca2b6c9b4807c7bc5f06
```

### Paso 3: Inicializar git flow
```bash
git flow init
```

**Responde a las preguntas (puedes presionar Enter para aceptar valores por defecto):**
```
Which branch should be used for bringing forth production releases?
- main (✓)

Which branch should be used for integration of the "next release"?
- develop (✓)

How to name your supporting branch prefixes?
Feature branches? [feature/] ✓
Bugfix branches? [bugfix/] ✓
Release branches? [release/] ✓
Hotfix branches? [hotfix/] ✓
Support branches? [support/] ✓
Version tag prefix? [] ✓
```

### Paso 4: Push de rama main inicial
```bash
git push -u origin main
```

---

## 📋 Estructura de Ramas en Git Flow

```
main (producción)
├── v1.0.0 (tags)
├── v1.1.0 (tags)
└── hotfix/X (correcciones urgentes)

develop (integración)
├── feature/autenticacion
├── feature/busqueda
├── feature/paginacion
├── release/1.1.0
└── bugfix/validacion
```

---

## 🔄 Flujo de Trabajo Típico

### 1️⃣ Crear Nueva Feature

```bash
# Crear rama de feature desde develop
git flow feature start autenticacion

# Esto crea: feature/autenticacion
# Y cambia automáticamente a esa rama

# Trabajar en la feature
git add .
git commit -m "feat: agregar autenticación JWT"
git add .
git commit -m "feat: validar tokens"

# Ver status
git flow feature
```

### 2️⃣ Publicar Feature en Remoto

```bash
# Si trabajas con un equipo
git flow feature publish autenticacion

# O manualmente
git push -u origin feature/autenticacion
```

### 3️⃣ Terminar Feature

```bash
# Terminar feature (merge a develop + eliminar rama)
git flow feature finish autenticacion

# Esto:
# - Hace merge a develop
# - Elimina rama local feature/autenticacion
# - Cambia a develop

# Push de develop
git push origin develop
```

### 4️⃣ Crear Release

```bash
# Cuando quieres preparar una versión
git flow release start 1.1.0

# Esto crea: release/1.1.0

# Cambios finales, testing, etc.
git add .
git commit -m "docs: actualizar versión a 1.1.0"

# Terminar release
git flow release finish 1.1.0

# Esto:
# - Merge a main y develop
# - Crea tag v1.1.0 en main
# - Elimina rama release/1.1.0

# Push a ambas ramas
git push origin main
git push origin develop
git push origin --tags
```

### 5️⃣ Hotfix para Producción

```bash
# Bug crítico en producción
git flow hotfix start db-connection-error

# Esto crea: hotfix/db-connection-error
# Basada en main

# Arreglar el bug
git add .
git commit -m "fix: reconexión a BD después de timeout"

# Terminar hotfix
git flow hotfix finish db-connection-error

# Esto:
# - Merge a main y develop
# - Crea tag v1.1.1 en main
# - Elimina rama hotfix/db-connection-error

# Push
git push origin main
git push origin develop
git push origin --tags
```

---

## 📊 Ejemplo Completo de Git Flow

### Día 1: Empezar Feature
```bash
git flow feature start jwt-auth
# Editar archivos...
git add .
git commit -m "feat: implementar autenticación JWT"
git flow feature publish jwt-auth
```

### Día 2: Otro dev trabaja en feature
```bash
git flow feature pull jwt-auth
# Editar archivos...
git add .
git commit -m "feat: agregar refresh tokens"
git push origin feature/jwt-auth
```

### Día 3: Terminar feature
```bash
git flow feature finish jwt-auth
# Automáticamente: merge a develop + elimina rama
git push origin develop
```

### Día 10: Preparar release
```bash
git flow release start 1.1.0
# Testing final...
git add .
git commit -m "docs: changelog v1.1.0"
git flow release finish 1.1.0
# Automáticamente: merge a main + develop + crea tag
git push origin main
git push origin develop
git push origin --tags
```

### Día 11: Bug crítico en producción
```bash
git flow hotfix start db-error
# Arreglar bug...
git add .
git commit -m "fix: error crítico de conexión"
git flow hotfix finish db-error
# Automáticamente: merge a main + develop + crea tag
git push origin main
git push origin develop
git push origin --tags
```

---

## 🔧 Comandos Útiles de Git Flow

```bash
# Ver features activas
git flow feature list

# Ver releases activas
git flow release list

# Ver hotfixes activos
git flow hotfix list

# Cambiar entre ramas manualmente
git checkout develop
git checkout feature/mi-feature

# Ver todas las ramas
git branch -a

# Ver tags (versiones)
git tag

# Pull de una feature específica
git flow feature pull nombre-feature

# Eliminar feature local
git branch -d feature/mi-feature

# Eliminar feature remota
git push origin --delete feature/mi-feature
```

---

## 🎯 Convenciones de Nombres

### Features
```
feature/autenticacion
feature/busqueda-avanzada
feature/paginacion
feature/upload-imagenes
```

### Bugfixes
```
bugfix/validacion-emails
bugfix/error-carrito
bugfix/cache-invalidation
```

### Releases
```
release/1.0.0
release/1.1.0
release/2.0.0-beta
```

### Hotfixes
```
hotfix/sql-injection
hotfix/timeout-db
hotfix/memory-leak
```

---

## 📈 Diagrama del Flujo

```
                       feature/x
                            |
                            v
develop -----[M]-------- [F] -----[M]------- develop
   |                                            |
   |                                            v
   |                                       release/1.0
   |                                            |
   |                                            v
   |                                        [T] [M]
   |                                            |
   +--------------------------------------------+
                                               |
main -----(v0.9)-----[M]------(v1.0)------(v1.1)---- main
                  ^                        ^
                  |                        |
              hotfix/0.9                hotfix/1.0

Leyenda:
[M] = Merge
[F] = Feature
[T] = Testing
v# = Tags de versión
```

---

## ⚠️ Buenas Prácticas

### DO ✅
- ✅ Una feature = una rama
- ✅ Commits descriptivos en features
- ✅ Hacer testing antes de terminar feature
- ✅ Actualizar `develop` antes de empezar feature
- ✅ Push regular de cambios
- ✅ Hacer code review antes de merge

### DON'T ❌
- ❌ Hacer push directo a main o develop
- ❌ Ramas feature que viven más de 2 semanas
- ❌ Commits sin descripción ("asdf", "fix")
- ❌ Mezclar múltiples features en una rama
- ❌ Olvidar hacer push de tags

---

## 🔐 Configuración de Protección (GitHub)

### En tu repo de GitHub:

1. Ir a **Settings** → **Branches**
2. Seleccionar **main** y activar:
   - [x] Require pull request reviews
   - [x] Require status checks to pass
   - [x] Include administrators
3. Seleccionar **develop** y activar:
   - [x] Require pull request reviews

---

## 📝 Ejemplo en el Proyecto RentStyle

### Inicializar
```bash
cd RENTSTYLE-BACK-END
git flow init
```

### Feature: Agregar Autenticación
```bash
git flow feature start autenticacion-jwt
# Crear archivo app/services/auth_service.py
# Actualizar app/__init__.py
# Crear blueprint para login
git add .
git commit -m "feat: implementar autenticación JWT"
git flow feature finish autenticacion-jwt
git push origin develop
```

### Feature: Agregar Búsqueda
```bash
git flow feature start busqueda-prendas
# Actualizar prendas_bp.py con filtros
git add .
git commit -m "feat: agregar búsqueda y filtros de prendas"
git flow feature finish busqueda-prendas
git push origin develop
```

### Release: v1.1.0
```bash
git flow release start 1.1.0
# Actualizar versión en README, ROADMAP, etc.
git add .
git commit -m "chore: bumped version to 1.1.0"
git flow release finish 1.1.0
git push origin main develop --tags
```

---

## 🆚 Git Flow vs. Trabajo Simple

| Aspecto | Simple Git | Git Flow |
|--------|-----------|----------|
| Ramas | main + features | main + develop + features + releases + hotfixes |
| Producción | Siempre de main | De main (tags) |
| Desarrollo | En features | En develop + features |
| Releases | Ad hoc | Planeadas con release/ |
| Hotfixes | Como feature | Rama dedicada |
| Complejidad | Baja | Media-Alta |
| Equipo | 1-3 personas | 3+ personas |

---

## 📚 Recursos

- [Documentación original de Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Git Flow Cheatsheet](https://cheatsheet.codementor.io/git)
- [GitHub Flow vs. Git Flow](https://lucamezzalira.com/2014/03/10/git-flow-vs-github-flow/)

---

**Git Flow es ideal para equipos que trabajan en versiones y releases planificadas. Para RentStyle con múltiples desarrolladores simultáneamente, es la opción recomendada.** 🚀

