# AGENTS.md — Tconecta Auth-Python

## Descripción

Microservicio de autenticación del sistema de tránsito Tconecta. API REST en Python con FastAPI, respaldada por PostgreSQL (usuarios) y MongoDB (billeteras). Emite tokens JWT (HS256) y gestiona transacciones de recarga/compra de tarjeta.

## Comandos

```bash
# Instalar dependencias (usa uv, no pip)
uv sync

# Desarrollo (con recarga automática)
uvicorn app.main:app --reload --port 5001

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Docker
docker compose up -d --build
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere PostgreSQL (`TransmetroAuthDb`) y MongoDB (`TransmetroUserDb`)
3. `JWT_SECRET` **debe ser idéntico** en todos los 6 servicios

## Arquitectura

- **FastAPI + Uvicorn** — Flujo asíncrono nativo (`async`/`await`)
- **SQLAlchemy (asyncpg)** — PostgreSQL para usuarios
- **Motor** — MongoDB asíncrono para billeteras (sin S2S)
- **python-jose[cryptography]** — Generación/verificación JWT
- **SlowAPI** — Rate limiting por IP
- **bcrypt** — Hash de contraseñas
- **Luhn** — Validación tarjetas antes de simular pago

## Base URL y Puerto

- **Base URL:** `/api`
- **Puerto dev:** 5001 | **Puerto Docker:** 8080

## Estructura de módulos

```
app/
├── main.py                    # FastAPI app + lifespan (auto-seed users)
├── config.py                  # Pydantic Settings
├── database.py                # SQLAlchemy engine/session
├── database_mongo.py          # Motor client
├── helpers/
│   ├── jwt.py                 # encode/decode JWT (HS256)
│   ├── luhn.py                # Algoritmo Luhn validación tarjetas
│   └── password.py            # bcrypt hash/verify
├── middlewares/
│   ├── validate_jwt.py        # JWT verification middleware
│   ├── require_admin.py       # Admin role guard
│   └── request_limit.py       # SlowAPI rate limiting
├── models/
│   ├── user.py                # SQLAlchemy User model
│   └── seed.py                # Auto-seed 3 usuarios al inicio
├── routers/
│   ├── auth.py                # /api/Auth/*
│   ├── transaction.py         # /api/transaction/*
│   └── wallet.py              # /api/wallets/*
├── schemas/
│   └── auth.py                # Pydantic request/response
└── services/
    ├── auth_service.py        # Registro, login, password reset
    ├── transaction_service.py # Recarga + compra tarjeta (Luhn + 1.5s delay)
    └── wallet_integration.py  # MongoDB wallets CRUD directo
```

## Endpoints Principales

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/Auth/register` | Registrar ciudadano | No |
| `POST` | `/Auth/login` | Login → retorna JWT | No |
| `POST` | `/Auth/recover-password` | Solicitar recuperación | No |
| `POST` | `/Auth/reset-password` | Restablecer contraseña | No |
| `GET` | `/Auth/users` | Listar usuarios | Admin |
| `POST` | `/Auth/register-admin` | Registrar admin | Admin |
| `POST` | `/transaction/recharge` | Recargar billetera (Luhn) | JWT |
| `POST` | `/transaction/purchase-card` | Comprar tarjeta Q20 | JWT |
| `GET` | `/wallets/balance` | Consultar saldo | JWT |

## Variables de entorno

```
NODE_ENV=development
PORT=5001
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/TransmetroAuthDb
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345
JWT_ISSUER=TransmetroAuthServer
JWT_AUDIENCE=TransmetroUsers
JWT_EXPIRES_IN=120
JWT_RESET_EXPIRES_IN=15
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
RATE_LIMIT_WINDOW=60
RATE_LIMIT_MAX=100
AUTH_RATE_LIMIT_MAX=10
```

## Detalles Críticos

- **Luhn validation** en `transaction_service.py` antes de simular pago (1.5s `asyncio.sleep`)
- **Compra tarjeta** hard-coded a **Q20.00** exactos
- **Auto-seed**: 3 usuarios creados al primer arranque (CUI: 2000000000001/2/3)
- **Rate limiting**: `/Auth/login` limitado a 10 req/min por IP
- **Sin migraciones**: Tablas PostgreSQL creadas con `Base.metadata.create_all` en lifespan
- **JWT claim Microsoft**: Token incluye `"http://schemas.microsoft.com/ws/2008/06/identity/claims/role"` por compatibilidad con backend .NET legacy