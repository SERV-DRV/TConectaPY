# AGENTS.md — TConectaPY (Monorepo Raíz)

## Qué es esto

6 microservicios Python independientes para el sistema de tránsito de Guatemala ("Transmetro Conecta"). **Sin workspace compartido, sin herramientas de monorepo** — cada subdirectorio es un proyecto Python independiente con su propio `pyproject.toml` y virtualenv.

## Servicios y puertos

| Directorio | Rol | Puerto | Framework | Base de datos |
|------------|-----|--------|-----------|---------------|
| `Auth-Python/` | Auth + ops de billetera | 5001 (dev) / 8080 (Docker) | FastAPI | PostgreSQL (`TransmetroAuthDb`) + MongoDB (`TransmetroUserDb`) |
| `Server-AdminPY/` | API CRUD admin | 3001 | FastAPI | MongoDB (`TransmetroAdminDb`) |
| `Server-ClientPY/` | API operaciones usuario | 3002 | FastAPI | MongoDB (`TransmetroUserDb`) |
| `Client-AdminPY/` | Panel admin web (SSR) | 5173 | FastAPI+Jinja2 | Ninguna (proxy a Server-Admin) |
| `Client-UserPY/` | App usuario web (SSR) | 5174 | FastAPI+Jinja2 | Ninguna (proxy a Server-Admin + Server-Client) |
| `Client-User-MobilePY/` | App móvil (Flet) | N/A (desktop) | Flet (Flutter) | SQLite local |

## Inicio rápido — correr todo localmente

```bash
# 1. Levantar bases de datos (desde Auth-Python/)
docker compose up postgres-db mongo-db -d

# 2. Levantar cada servicio (cada uno en su terminal, desde su directorio):
cd Auth-Python && uv sync && uvicorn app.main:app --reload --port 5001
cd Server-AdminPY && pip install -e . && uvicorn app.main:app --reload --port 3001
cd Server-ClientPY && pip install -e . && uvicorn app.main:app --reload --port 3002
cd Client-AdminPY && pip install -e . && uvicorn app.main:app --reload --port 5173
cd Client-UserPY && pip install -e . && uvicorn app.main:app --reload --port 5174
cd Client-User-MobilePY && pip install -e . && flet run app/main.py
```

O usar el Docker Compose completo desde `Auth-Python/`:
```bash
cd Auth-Python && docker compose up --build
```

## Crítico: JWT_SECRET debe ser idéntico en todos lados

Todos los servicios comparten `JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345`. Si lo cambiás en un servicio, actualizalo en todos los `.env` y `docker-compose.yml`. Las diferencias causan fallos silenciosos de auth (401s).

## Bases de datos

- **PostgreSQL 16** — Solo lo usa Auth-Python para cuentas de usuario (tabla `transmetro_users`). Las tablas se crean automáticamente con `Base.metadata.create_all` al iniciar. **Sin Alembic / sin migraciones.**
- **MongoDB 6.0** — Lo usan Server-Admin (`TransmetroAdminDb`: estaciones, rutas, buses, alertas), Server-Client (`TransmetroUserDb`: perfiles, tours, billeteras), y Auth-Python (`TransmetroUserDb`: billeteras directamente).
- `Server-AdminPY` auto-siembra datos de tránsito desde `app/data/transmetro.geojson` en el primer arranque cuando `AUTO_SEED=true` y las colecciones están vacías.

## Setup de cada proyecto

Cada subdirectorio usa:
```bash
pip install -e .        # instalar en modo editable
# luego correr con uvicorn o flet
```

Auth-Python usa `uv sync` en vez de pip (tiene `uv.lock`).

## Arquitectura JWT compartida

- Auth-Python **genera** JWTs (HS256, `python-jose`).
- Todos los demás servicios **verifican** JWTs — nunca generan tokens.
- El token incluye tanto el claim `"role"` como el claim estilo Microsoft `"http://schemas.microsoft.com/ws/2008/06/identity/claims/role"` por compatibilidad.
- Las apps cliente (Admin/User) guardan el JWT en sesiones cookie firmadas via `SessionMiddleware` y decodifican el payload **sin verificación de firma** (confiando en el auth-server).

## Variables de entorno

Copiar `.env.example` a `.env` en cada subdirectorio. Variables clave:
- `JWT_SECRET` — debe ser idéntico en los 6 servicios
- `MONGODB_URI` — apunta a la base de datos correcta por servicio
- `INTERNAL_SECRET` — Server-Client usa esto para endpoints server-to-server (header `x-internal-secret`)

## Dependencias de servicios (orden de arranque)

1. PostgreSQL + MongoDB
2. Auth-Python (depende de ambas bases)
3. Server-Admin + Server-Client (dependen de MongoDB)
4. Client-Admin + Client-User (dependen de Auth + Server-Admin/Server-Client)

## Qué hace cada servicio

- **Auth-Python**: Registro/login, emisión de JWT, recarga de billetera + compra de tarjeta (MongoDB directo), rate limiting (SlowAPI), auto-siembra 3 usuarios en el primer arranque.
- **Server-Admin**: CRUD de estaciones, rutas, buses, alertas. Consultas geoespaciales en MongoDB. Los endpoints de `/buses` **no requieren auth** (intencional).
- **Server-Client**: Balance/historial de billetera, planificación de tours con deducción de tarifa, perfiles de usuario. Tiene endpoints internos S2S (`/wallets/initialize`, `/wallets/recharge`) protegidos con `x-internal-secret`.
- **Client-Admin**: Panel admin server-rendered (FastAPI + Jinja2 + Tailwind + Leaflet + Chart.js). Proxy de todas las llamadas API a Server-Admin.
- **Client-User**: App de usuario server-rendered. Proxy a Server-Admin (rutas/estaciones/alertas) + Server-Client (billetera/tours) + Auth (login/recarga).
- **Client-User-Mobile**: App móvil con Flet que conecta a Auth + Server-Admin + Server-Client. Build de APK con Buildozer.

## Detalles que vale la pena saber

- HTMX está cargado en las plantillas de Client-Admin y Client-User pero **no se usa** — todas las interacciones son recargas de página completa.
- `decode_jwt()` en las apps cliente usa decodificación base64 sin verificación criptográfica — confía en el firmado de la cookie de sesión para seguridad.
- Auth-Python tiene `asyncio.sleep(1.5)` en endpoints de transacción para simular latencia de procesamiento de pago.
- La compra de tarjeta en Auth-Python está hard-coded a exactamente Q20.00.
- Server-Client usa `PyJWT` mientras que Auth-Python y Server-Admin usan `python-jose` para JWT — librerías distintas, mismo secreto.
- `Server-ClientPY` llama `load_dotenv()` a nivel de módulo en `main.py`; los demás servicios dependen de que las env vars estén seteadas externamente.
- La documentación Swagger (`/docs`) solo está disponible cuando `NODE_ENV=development`.
