# AGENTS.md — Tconecta Client User (Python)

## Descripción

Aplicación de usuario del sistema de tránsito Tconecta. Aplicación web server-rendered en Python con FastAPI + Jinja2 + HTMX. Permite a los usuarios planificar viajes, gestionar billetera virtual, explorar rutas/estaciones y ver alertas de servicio. Conecta a 3 microservicios: Auth-Server (8080), Server-Admin (3001), Server-Client (3002).

## Comandos

```bash
# Instalar dependencias
pip install -e .

# Desarrollo
uvicorn app.main:app --reload --port 5174

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 5174
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere Auth-Server en puerto 8080
3. Requiere Server-Admin en puerto 3001
4. Requiere Server-Client en puerto 3002

## Arquitectura

- **FastAPI + Jinja2** — Server-side rendering
- **HTMX** — Cargado en base.html pero no usado activamente (interacciones son full-page reloads)
- **Tailwind CSS** — Estilos vía CDN
- **Leaflet** — Mapas interactivos para planificador de rutas
- **Chart.js** — Gráficas de perfil (gasto, distancia)
- **httpx** — Cliente HTTP async para 3 backends
- **python-jose** — Decodificación JWT

## APIs a las que conecta

### Auth-Server (`http://localhost:8080/api`)
- `POST /Auth/login` — Login
- `POST /Auth/register` — Registro
- `GET /Auth/me/email` — Obtener email
- `PUT /Auth/update-email` — Actualizar email
- `POST /Transaction/recharge` — Recargar billetera
- `POST /Transaction/purchase-card` — Comprar tarjeta

### Server-Admin (`http://localhost:3001/TCONECTA/v1`)
- `GET /alerts` — Alertas de servicio
- `GET /stations/all?status=ACTIVE` — Estaciones activas
- `GET /roads/all?status=ACTIVE` — Rutas activas
- `GET /roads?page=N&limit=6` — Rutas paginadas
- `GET /stations?page=N&limit=9` — Estaciones paginadas

### Server-Client (`http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1`)
- `GET /wallets/balance` — Saldo billetera
- `GET /wallets/history?page=N&limit=10` — Historial recargas
- `GET /tours/history` — Historial viajes
- `POST /tours/plan` — Pagar y registrar viaje

## Estructura

```
app/
├── main.py              # FastAPI app, lifespan, sesión
├── config.py            # URLs de los 3 backends
├── api_client.py        # Cliente httpx para los 3 microservicios
├── routers/
│   ├── auth.py          # Login/registro/logout
│   ├── planner.py       # Planificador de rutas con mapa
│   ├── wallet.py        # Billetera: recarga, compra, historial
│   ├── explore.py       # Explorar rutas y estaciones
│   ├── alerts.py        # Alertas de servicio
│   └── profile.py       # Perfil, estadísticas, email
├── templates/
│   ├── base.html        # Layout con navbar, Tailwind, HTMX
│   ├── auth/login.html
│   ├── planner/index.html   # Mapa Leaflet + planificador
│   ├── wallet/index.html    # Tarjeta visual + tabs
│   ├── explore/index.html   # Grid de rutas/estaciones
│   ├── alerts/index.html    # Tarjetas de alertas
│   └── profile/index.html   # Stats, charts, email
└── static/
```

## Rutas del Cliente

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Redirect a /planner | No |
| GET/POST | `/auth/login` | Login/registro | No |
| POST | `/auth/logout` | Logout | No |
| GET | `/planner` | Planificador con mapa | Sí |
| POST | `/planner/pay` | Pagar viaje | Sí |
| GET | `/wallet` | Billetera (tabs) | Sí |
| POST | `/wallet/recharge` | Recargar saldo | Sí |
| POST | `/wallet/purchase-card` | Comprar tarjeta | Sí |
| GET | `/explore` | Explorar rutas/estaciones | Sí |
| GET | `/alerts` | Alertas de servicio | Sí |
| GET | `/profile` | Perfil + estadísticas | Sí |
| POST | `/profile/update-email` | Actualizar email | Sí |

## Variables de entorno

```
SECRET_KEY=<clave para sesiones FastAPI>
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
```
