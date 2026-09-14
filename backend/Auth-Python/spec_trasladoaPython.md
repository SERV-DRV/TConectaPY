# Especificación de Traslado: Auth-Node → Auth-Python (FastAPI)

## Resumen

Conversión del microservicio de autenticación de Node.js/Express 5/Sequelize/PostgreSQL a Python/FastAPI/SQLAlchemy 2.0 Async/PostgreSQL. Auth-Python genera JWTs (HS256) y gestiona registro, login, recuperación de contraseña, y operaciones de billetera vía MongoDB directo.

## Tecnología de Origen → Destino

| Componente | Original (Node.js) | Equivalente Python |
|---|---|---|
| Framework | Express 5 | FastAPI |
| ORM/DB Driver | Sequelize 6 (sync) | SQLAlchemy 2.0 (async) + asyncpg |
| Validación body | express-validator + `validateSchema` | Pydantic models con `AliasChoices` |
| Normalización body | `normalize-body.js` (camelCase→PascalCase) | Pydantic `alias_choices` + `populate_by_name=True` |
| JWT creation | jsonwebtoken (HS256) | python-jose (HS256) |
| JWT verification | `verifyAccessToken()` helper | `python-jose.decode()` |
| Password hashing | bcryptjs (salt rounds: 10) | bcrypt (native) |
| Rate limiting | express-rate-limit | SlowAPI (`@limiter.limit`) |
| Env vars | dotenv + `config.js` | pydantic-settings (`BaseSettings`) |
| DB sync/migrations | `sequelize.sync({ alter: true })` | `Base.metadata.create_all()` (sin Alembic) |
| Auto-seeder | `models/seed.js` on startup | `models/seed.py` en `lifespan` |
| Middleware auth | `validate-jwt.js` + `require-admin.js` | `Depends(validate_jwt)` + `Depends(require_admin)` |
| Error handler | `error-handler.js` global | `@app.exception_handler` global |
| CORS | cors middleware | CORSMiddleware |
| Logger | morgan | print() / logging (dev) |
| HTTP client (S2S) | axios | httpx (async) |
| Swagger docs | swagger-ui-express | FastAPI `/docs` (auto) |

## `__init__.py` — Estructura de Paquetes

```
app/
├── __init__.py              # Vacío (marca de paquete)
├── config.py                # Settings (pydantic-settings)
├── database.py              # SQLAlchemy async engine + session
├── database_mongo.py        # Motor (MongoDB driver async)
├── main.py                  # FastAPI app + lifespan + routers
├── helpers/
│   ├── __init__.py
│   ├── jwt.py               # jwt.encode/decode (python-jose)
│   ├── luhn.py              # Algoritmo Luhn para validación de tarjeta
│   └── password.py          # bcrypt hash/verify
├── middlewares/
│   ├── __init__.py
│   ├── request_limit.py     # SlowAPI rate limiting
│   ├── require_admin.py     # Depends: verificar rol Admin
│   └── validate_jwt.py      # Depends: extraer y verificar JWT
├── models/
│   ├── __init__.py
│   ├── seed.py              # Auto-seed 3 usuarios (2 admin + 1 ciudadano)
│   └── user.py              # SQLAlchemy model: transmetro_users
├── routers/
│   ├── __init__.py
│   ├── auth.py              # /api/Auth/* — register, login, reset, users, email
│   ├── transaction.py       # /api/transaction/* — recharge, purchase-card
│   └── wallet.py            # /api/wallets/* — endpoints wallet
├── schemas/
│   ├── __init__.py
│   └── auth.py              # Pydantic request/response schemas
└── services/
    ├── __init__.py
    ├── auth_service.py      # Lógica de negocio auth
    ├── transaction_service.py   # Lógica de transacciones
    └── wallet_integration.py    # Operaciones MongoDB wallet (directo)
```

## Estructura de Archivos: Node.js → Python

```
NODE.JS (Auth-Node)                         PYTHON (Auth-Python)
──────────────────────────────────          ─────────────────────────────────
index.js                                    app/main.py
configs/app.js                              app/main.py (FastAPI app + middleware)
configs/config.js                           app/config.py (BaseSettings)
configs/db.js                               app/database.py (SQLAlchemy async)
configs/cors-configuration.js               CORSMiddleware en app/main.py
configs/helmet-configuration.js             No necesario (FastAPI no lo requiere)
helpers/async-handler.js                    async/await nativo (sin wrapper)
helpers/jwt.js                              app/helpers/jwt.py (python-jose)
helpers/luhn.js                             app/helpers/luhn.py
helpers/password.js                         app/helpers/password.py (bcrypt)
middlewares/validate-jwt.js                 app/middlewares/validate_jwt.py
middlewares/require-admin.js                app/middlewares/require_admin.py
middlewares/error-handler.js                @app.exception_handler en app/main.py
middlewares/normalize-body.js               Pydantic AliasChoices (eliminado)
middlewares/request-limit.js                app/middlewares/request_limit.py (SlowAPI)
middlewares/validate-schema.js              Pydantic validation automática
models/user.model.js                        app/models/user.py (SQLAlchemy)
models/seed.js                              app/models/seed.py
src/auth/auth.routes.js                     app/routers/auth.py
src/auth/auth.controller.js                 app/routers/auth.py (handlers inline)
src/auth/auth.service.js                    app/services/auth_service.py
src/auth/auth.validators.js                 app/schemas/auth.py (Pydantic)
src/transaction/transaction.routes.js       app/routers/transaction.py
src/transaction/transaction.controller.js   app/routers/transaction.py
src/transaction/transaction.service.js      app/services/transaction_service.py
src/transaction/wallet.integration.js       app/services/wallet_integration.py
```

## Mapeo de Módulos

### Configuración
- `configs/config.js` (objeto plano con `process.env`) → `app/config.py` (Pydantic `BaseSettings` con validación de tipos y `.env` automático)
- `dotenv.config()` → `SettingsConfigDict(env_file=".env")`

### Base de datos PostgreSQL
- `configs/db.js` (Sequelize `new Sequelize()` + `sync({ alter: true })`) → `app/database.py` (`create_async_engine` + `Base.metadata.create_all()`)
- `models/user.model.js` (Sequelize `define()`) → `app/models/user.py` (SQLAlchemy `mapped_column`)
- Convención: `timestamps: false` global → `created_at` se gestiona manualmente

### JWT
- `helpers/jwt.js` (`jwt.sign()`, `jwt.verify()`) → `app/helpers/jwt.py` (`jwt.encode()`, `jwt.decode()` con `python-jose`)
- Mismo algoritmo: HS256
- Mismos claims: `sub` (userId), `cui`, `role`, `iss`, `aud`

### Middleware de autenticación
- `middlewares/validate-jwt.js` (extrae de `Authorization` o `x-token`, verifica en BD) → `app/middlewares/validate_jwt.py` (FastAPI `Depends`, misma lógica)
- `middlewares/require-admin.js` → `app/middlewares/require_admin.py` (FastAPI `Depends`)

### Rutas de Auth
- `auth.routes.js` (Router + `authRateLimit` + `normalizeAuthBody` + validators + controller) → `app/routers/auth.py` (`APIRouter` + `@limiter.limit("10/minute")` + Pydantic body automático)
- `normalizeAuthBody` se **elimina** — Pydantic `AliasChoices("CUI", "cui")` acepta ambos formatos

### Pydantic Schemas (equivalente a auth.validators.js)

```python
# Equivalente a registerValidation + loginValidation en auth.validators.js
class RegisterRequest(BaseAuthSchema):
    CUI: str = Field(
        validation_alias=AliasChoices("CUI", "cui"),  # acepta camelCase y PascalCase
        min_length=13, max_length=13, pattern=r"^\d{13}$"
    )
    Email: EmailStr = Field(validation_alias=AliasChoices("Email", "email"))
    Password: str = Field(validation_alias=AliasChoices("Password", "password"), min_length=6)

class LoginRequest(BaseAuthSchema):
    CUI: str = Field(validation_alias=AliasChoices("CUI", "cui"), min_length=13, max_length=13)
    Password: str = Field(validation_alias=AliasChoices("Password", "password"))
```

### Respuesta de error
- Node.js: `{ StatusCode, Message, Detailed }` (PascalCase) → Python: **mismo formato** (via `@app.exception_handler`)

### Rate Limiting
- `express-rate-limit` (100/min global, 10/min auth) → SlowAPI `@limiter.limit("10/minute")` por endpoint

### Auto-seeder
- `models/seed.js` (Sequelize bulkCreate) → `app/models/seed.py` (SQLAlchemy `exec_driver_session`)

### S2S a Server-Client (Wallet)
- `src/transaction/wallet.integration.js` (axios) → `app/services/wallet_integration.py` (httpx async)
- Header `x-internal-secret` con `INTERNAL_SECRET`

## Variables de entorno

```
NODE_ENV=development
PORT=5001
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/TransmetroAuthDb
JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345
JWT_ISSUER=TransmetroAuthServer
JWT_AUDIENCE=TransmetroUsers
JWT_EXPIRES_IN=120
JWT_RESET_EXPIRES_IN=15
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
ALLOWED_ORIGINS=
INTERNAL_SECRET=SuperSecretS2S_Transmetro2026
```

## Detalles Importantes

- **Rutas case-sensitive:** `/api/Auth` (A mayúscula) y `/api/transaction` (minúscula) — replicar exactamente el contrato de .NET
- **CUI:** Exactamente 13 dígitos numéricos, unique en PostgreSQL
- **Roles:** `"User"` o `"Admin"` (strings, no enum)
- **JWT_EXPIRES_IN:** En Node.js es string `"2h"`, en Python es int `120` (minutos) — conversión manual
- **MongoDB wallet:** Auth-Python accede directamente a `TransmetroUserDb` para operaciones de billetera (no usa S2S para todo)
- **`asyncio.sleep(1.5)`** en endpoints de transacción para simular latencia de pago
- **Compra de tarjeta:** Hard-coded a Q20.00
- **Sin Alembic:** `Base.metadata.create_all()` al iniciar — cambios de schema se hacen en el modelo y se reinicia
