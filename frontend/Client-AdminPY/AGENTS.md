# AGENTS.md — Tconecta Client Admin (Python)

## Descripción

Panel de administración del sistema de tránsito Tconecta. Aplicación web server-rendered en Python con FastAPI + Jinja2. Conecta al microservicio Server-Admin (puerto 3001) para CRUD de estaciones, rutas, buses, alertas y usuarios. Autenticación JWT contra Auth-Python (puerto 8080).

## Comandos

```bash
# Instalar dependencias
pip install -e .

# Desarrollo
uvicorn app.main:app --reload --port 5173

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 5173
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere Server-Admin ejecutándose en puerto 3001
3. Requiere Auth-Server ejecutándose en puerto 8080
4. `SECRET_KEY` para sesiones de FastAPI

## Arquitectura

- **FastAPI** — Backend framework con Jinja2 para templates server-side
- **HTMX** — Cargado en base.html pero no usado activamente (interacciones son full-page reloads)
- **Tailwind CSS** — Estilos vía CDN
- **Leaflet** — Mapas interactivos vía CDN
- **Chart.js** — Gráficas del dashboard vía CDN
- **httpx** — Cliente HTTP async para comunicarse con Server-Admin y Auth-Server
- **python-jose** — Decodificación de tokens JWT

## Base URL

- **Cliente Admin:** `http://localhost:5173`
- **Server Admin:** `http://localhost:3001/TCONECTA/v1`
- **Auth Server:** `http://localhost:8080/api`

## Estructura

```
app/
├── main.py              # FastAPI app, lifespan, middleware de sesión
├── config.py            # Variables de entorno y URLs de backends
├── api_client.py        # Cliente httpx para Server-Admin y Auth-Server
├── routers/
│   ├── auth.py          # Login/logout/forgot-password
│   ├── dashboard.py     # Overview con estadísticas
│   ├── roads.py         # CRUD rutas + mapa Leaflet
│   ├── stations.py      # CRUD estaciones + mapa Leaflet
│   ├── buses.py         # CRUD buses
│   ├── alerts.py        # CRUD alertas
│   └── users.py         # Gestión de usuarios admin
├── templates/
│   ├── base.html        # Layout base (Tailwind, HTMX, navbar, sidebar)
│   ├── auth/login.html
│   ├── dashboard/index.html
│   ├── roads/index.html
│   ├── stations/index.html
│   ├── buses/index.html
│   ├── alerts/index.html
│   └── users/index.html
└── static/              # CSS/JS custom si se necesita
```

## Rutas del Cliente

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Redirect a /dashboard | No |
| GET/POST | `/auth/login` | Login | No |
| POST | `/auth/logout` | Logout | No |
| GET | `/dashboard` | Dashboard overview | Sí |
| GET | `/roads` | Lista rutas (HTMX paginación) | Sí |
| POST | `/roads` | Crear ruta | Sí+Admin |
| PUT | `/roads/{id}` | Actualizar ruta | Sí+Admin |
| PUT | `/roads/{id}/status` | Cambiar estado | Sí+Admin |
| GET | `/stations` | Lista estaciones | Sí |
| POST | `/stations` | Crear estación | Sí+Admin |
| PUT | `/stations/{id}` | Actualizar estación | Sí+Admin |
| PUT | `/stations/{id}/status` | Cambiar estado | Sí+Admin |
| GET | `/buses` | Lista buses | Sí |
| POST | `/buses` | Crear bus | Sí |
| PUT | `/buses/{id}` | Actualizar bus | Sí |
| PATCH | `/buses/{id}/status` | Cambiar estado | Sí |
| GET | `/alerts` | Lista alertas | Sí |
| POST | `/alerts` | Crear alerta | Sí+Admin |
| PUT | `/alerts/{id}/status` | Resolver alerta | Sí+Admin |
| GET | `/users` | Lista usuarios | Sí+Admin |
| POST | `/users` | Crear admin | Sí+Admin |

## API Calls al Server-Admin (via httpx)

Las llamadas al backend se hacen en `api_client.py` usando `httpx.AsyncClient` con base URL `http://localhost:3001/TCONECTA/v1`. El token JWT se envía como `Authorization: Bearer <token>`.

## Variables de entorno

```
SECRET_KEY=<clave para sesiones FastAPI>
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
```
