# AGENTS.md — TConectaPY (Monorepo Raíz)

**6 microservicios Python independientes** para "Transmetro Conecta" (sistema de tránsito Guatemala). **Sin workspace compartido** — cada subdirectorio es un proyecto Python con su propio `pyproject.toml` y virtualenv.

---

## Servicios y Puertos

| Directorio | Rol | Puerto (dev) | Framework | Base de datos |
|------------|-----|--------------|-----------|---------------|
| `backend/Auth-Python/` | Auth + wallet ops | 5001 / 8080 (Docker) | FastAPI | PostgreSQL (`TransmetroAuthDb`) + MongoDB (`TransmetroUserDb`) |
| `backend/Server-AdminPY/` | API CRUD admin | 3001 | FastAPI | MongoDB (`TransmetroAdminDb`) |
| `backend/Server-ClientPY/` | API operaciones usuario | 3002 | FastAPI | MongoDB (`TransmetroUserDb`) |
| `frontend/Client-AdminPY/` | Panel admin web (SSR) | 5173 | FastAPI+Jinja2 | Proxy a Server-Admin |
| `frontend/Client-UserPY/` | App usuario web (SSR) | 5174 | FastAPI+Jinja2 | Proxy a Server-Admin + Server-Client |
| `mobile/Client-User-MobilePY/` | App móvil (Flet) | N/A (desktop) | Flet (Flutter) | SQLite local |

---

## Inicio Rápido

```bash
# 1. Bases de datos (desde Auth-Python)
cd backend/Auth-Python && docker compose up postgres-db mongo-db -d

# 2. Cada servicio en su terminal (desde su directorio):
cd backend/Auth-Python && uv sync && uvicorn app.main:app --reload --port 5001
cd backend/Server-AdminPY && pip install -e . && uvicorn app.main:app --reload --port 3001
cd backend/Server-ClientPY && pip install -e . && uvicorn app.main:app --reload --port 3002
cd frontend/Client-AdminPY && pip install -e . && uvicorn app.main:app --reload --port 5173
cd frontend/Client-UserPY && pip install -e . && uvicorn app.main:app --reload --port 5174
cd mobile/Client-User-MobilePY && pip install -e . && flet run app/main.py
```

**Docker Compose completo** (levanta todo):
```bash
cd backend/Auth-Python && docker compose up --build
```

---

## ⚠️ Crítico: JWT_SECRET Idéntico en Todos los Servicios

`JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345` debe ser **exactamente igual** en:
- Todos los `.env` de cada servicio
- `docker-compose.yml` de Auth-Python

Diferencias → fallos silenciosos de auth (401s).

---

## Bases de Datos

- **PostgreSQL 16** — Solo Auth-Python (`transmetro_users`). Tablas auto-creadas con `Base.metadata.create_all`. **Sin Alembic / sin migraciones.**
- **MongoDB 6.0** — 
  - Server-Admin: `TransmetroAdminDb` (estaciones, rutas, buses, alertas)
  - Server-Client: `TransmetroUserDb` (perfiles, tours, billeteras)
  - Auth-Python: `TransmetroUserDb` (billeteras directo, sin S2S)
- **Auto-seed**: Server-Admin siembra `app/data/transmetro.geojson` al arrancar si `AUTO_SEED=true` y colecciones vacías.

---

## Arquitectura JWT Compartida

- **Auth-Python genera** JWTs (HS256, `python-jose`).
- **Otros servicios solo verifican** — nunca generan tokens.
- Token incluye `"role"` + claim Microsoft `"http://schemas.microsoft.com/ws/2008/06/identity/claims/role"` (compatibilidad).
- Apps cliente (Admin/User) guardan JWT en **cookies firmadas** (`SessionMiddleware`) y decodifican payload **sin verificación de firma** (confían en auth-server).

---

## Variables de Entorno (por servicio)

| Servicio | Archivo | Variables clave |
|----------|---------|-----------------|
| Auth-Python | `backend/Auth-Python/.env.example` | `JWT_SECRET`, `DATABASE_URL`, `MONGODB_URI`, `PORT=5001` |
| Server-Admin | `backend/Server-AdminPY/.env.example` | `JWT_SECRET`, `MONGODB_URI=.../TransmetroAdminDb`, `PORT=3001`, `AUTO_SEED=true` |
| Server-Client | `backend/Server-ClientPY/.env.example` | `JWT_SECRET`, `MONGODB_URI=.../TransmetroUserDb`, `PORT=3002`, `INTERNAL_SECRET` |
| Client-Admin | `frontend/Client-AdminPY/.env.example` | `SECRET_KEY`, `AUTH_URL`, `ADMIN_URL` |
| Client-User | `frontend/Client-UserPY/.env.example` | `SECRET_KEY`, `AUTH_URL`, `ADMIN_URL`, `CLIENT_URL` |
| Mobile | `mobile/Client-User-MobilePY/.env.example` | `AUTH_URL`, `ADMIN_URL`, `CLIENT_URL` |

**Copiar `.env.example` → `.env` en cada directorio antes de arrancar.**

---

## Orden de Arranque (Dependencias)

1. PostgreSQL + MongoDB
2. Auth-Python (necesita ambas BDs)
3. Server-Admin + Server-Client (necesitan MongoDB)
4. Client-Admin + Client-User (necesitan Auth + Server-Admin/Server-Client)

---

## Qué Hace Cada Servicio

- **Auth-Python**: Registro/login, emisión JWT, recarga wallet + compra tarjeta (MongoDB directo), rate limiting (SlowAPI), auto-siembra 3 usuarios al iniciar.
- **Server-Admin**: CRUD estaciones, rutas, buses, alertas. Geoespacial MongoDB. `/buses` **sin auth** (intencional).
- **Server-Client**: Balance/historial wallet, planificación tours con deducción tarifa, perfiles. Endpoints S2S (`/wallets/initialize`, `/wallets/recharge`) con header `x-internal-secret`.
- **Client-Admin**: Panel admin SSR (FastAPI+Jinja2+Tailwind+Leaflet+Chart.js). Proxy a Server-Admin.
- **Client-User**: App usuario SSR. Proxy a Server-Admin (rutas/estaciones/alertas) + Server-Client (wallet/tours) + Auth (login/recarga).
- **Client-User-Mobile**: App móvil Flet → Auth + Server-Admin + Server-Client. Build APK con Buildozer.

---

## Detalles Operativos Clave

- **HTMX** cargado en templates Client-Admin/User pero **no se usa** — interacciones son full-page reloads.
- `decode_jwt()` en apps cliente = decodificación base64 **sin verificación criptográfica**.
- Auth-Python: `asyncio.sleep(1.5)` en endpoints de transacción (simula latencia pago).
- Compra tarjeta en Auth-Python **hard-coded a Q20.00**.
- Server-Client usa `PyJWT`; Auth-Python y Server-Admin usan `python-jose` — librerías distintas, mismo secreto.
- Server-Client llama `load_dotenv()` a nivel módulo en `main.py`; otros dependen de env vars externas.
- Swagger `/docs` solo disponible con `NODE_ENV=development`.

---

## Testing — Playwright E2E

```bash
# Instalar
pip install playwright pytest pytest-html && playwright install chromium

# Correr tests
pytest test/ -v                    # Todos
pytest test/ -v --headed           # Ver navegador
pytest test/ -v --html=report.html # Reporte HTML
pytest test/test_admin_buses.py -v # Test específico
pytest test/ -v -k "admin"         # Solo tests admin
pytest test/ -v -k "user"          # Solo tests user
pytest test/ -v -x                 # Parar en primer error
```

**Credenciales de test:**
| CUI | Contraseña | Rol | Páginas |
|-----|------------|-----|---------|
| `1000000000001` | `Admin123!` | Admin | Dashboard, Roads, Stations, Buses, Alerts, Users |
| `2000000000002` | `Usuario123!` | User | Planner, Wallet, Explore, Alerts, Profile |

**Rate limiting**: Auth server retorna 429. `conftest.py` tiene retry automático (3 intentos, 5s espera).

---

## CI/CD — GitHub Actions

Archivo: `.github/workflows/playwright-tests.yml`

**Triggers**: push a `main`/`develop`, PR a `main`, manual dispatch.

**Pasos**: Checkout → Docker services (Auth-Python compose) → Wait health checks → Python 3.11 + deps → `pytest` → Upload report/artifacts → Stop Docker.

---

## App Móvil — Build APK

```bash
cd mobile/Client-User-MobilePY
docker compose up --build
# APK en: bin/tconecta-1.0.0-arm64-v8a-debug.apk
```

**buildozer.spec** clave:
- `requirements = python3,flet,flet-map,httpx,python-jose[cryptography]`
- `android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION`
- `android.archs = arm64-v8a`

---

## Estructura de Directorios (Resumen)

```
TConectaPY/
├── .github/workflows/playwright-tests.yml
├── README.md
├── pyproject.toml              # Solo deps de test (playwright, pytest)
├── test/                       # Playwright E2E tests
├── backend/
│   ├── Auth-Python/            # uv sync, uv.lock, Dockerfile, docker-compose.yml
│   ├── Server-AdminPY/         # pip install -e ., auto-seeder GeoJSON
│   └── Server-ClientPY/        # pip install -e ., PyJWT (no python-jose)
├── frontend/
│   ├── Client-AdminPY/         # Jinja2 + Tailwind + Leaflet + Chart.js
│   └── Client-UserPY/          # Jinja2 + Leaflet + Chart.js
└── mobile/
    └── Client-User-MobilePY/   # Flet, buildozer, Dockerfile, docker-compose.yml
```

---

## AGENTS.md por Servicio

Cada subdirectorio tiene su propio `AGENTS.md` con detalles específicos:
- `backend/Auth-Python/AGENTS.md`
- `backend/Server-AdminPY/AGENTS.md`
- `backend/Server-ClientPY/AGENTS.md`
- `frontend/Client-AdminPY/AGENTS.md`
- `frontend/Client-UserPY/AGENTS.md`
- `mobile/Client-User-MobilePY/AGENTS.md`

---

## Referencias Rápidas

- **README.md** — Documentación completa: modelos de datos, algoritmos (Luhn, Haversine, tarifas, JWT, geocoding, OSRM), endpoints API, despliegue Render, estructura completa.
- **pyproject.toml (raíz)** — Solo dependencias de testing.
- **docker-compose.yml (Auth-Python)** — Orquestación completa de todos los servicios.