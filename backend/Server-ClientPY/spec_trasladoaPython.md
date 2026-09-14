# Especificación de Traslado: Server-Client (Node.js) → Server-ClientPY (FastAPI)

## Resumen

Conversión del microservicio de operaciones de usuario de Node.js/Express 5/Mongoose/MongoDB a Python/FastAPI/Motor/MongoDB. Gestiona billetera virtual (saldo, recargas, historial), planificación de tours (tarifas por sistema, viajes de cortesía) y perfiles de usuario. Incluye endpoints S2S protegidos con `x-internal-secret`.

## Tecnología de Origen → Destino

| Componente | Original (Node.js) | Equivalente Python |
|---|---|---|
| Framework | Express 5 | FastAPI |
| MongoDB ODM | Mongoose 9 | Motor 3.6 (async nativo) |
| JWT verification | express-validator + hand-rolled `auth-validators.js` | PyJWT + `Depends(verify_token)` |
| S2S auth | `x-internal-secret` header check | `Depends(verify_internal_secret)` |
| Validación body | hand-rolled validators | Pydantic models |
| Password hashing | argon2-cffi | argon2-cffi (mismo) |
| Geo utilities | `src/utils/geo-utils.js` (Haversine) | `app/utils/geo_utils.py` |
| Encryption | `src/utils/encrypt.js` | `app/utils/encryption.py` |
| Rate limiting | express-rate-limit | No implementado (pendiente) |
| Env vars | dotenv + `process.env` | python-dotenv (`load_dotenv()`) |
| HTTP client | axios (para S2S) | httpx (async) |
| CORS | cors middleware | CORSMiddleware |
| Logger | morgan | print() / logging |
| Error handler | `handle-errors.js` | FastAPI exception handlers |

## `__init__.py` — Estructura de Paquetes

```
app/
├── __init__.py              # Vacío
├── main.py                  # FastAPI app + lifespan + load_dotenv()
├── configs/
│   ├── __init__.py
│   ├── app.py               # register_routes(app)
│   └── database.py          # Motor: connect_db, get_db, close_db
├── middlewares/
│   ├── __init__.py
│   ├── profiles_validators.py   # Pydantic validators para profiles
│   ├── tours_validators.py      # Pydantic validators para tours
│   ├── validate_jwt.py          # Depends: JWT verification (PyJWT)
│   ├── verify_internal_secret.py # Depends: x-internal-secret check
│   └── wallets_validators.py    # Pydantic validators para wallets
├── profiles/
│   ├── __init__.py
│   ├── controller.py        # GET/PUT /me
│   ├── model.py             # Pydantic model: ProfileResponse, ProfileUpdate
│   └── routes.py            # APIRouter: /profiles
├── tours/
│   ├── __init__.py
│   ├── controller.py        # GET history, POST plan (fare logic)
│   ├── model.py             # Pydantic model: PlanTourBody, TourResponse
│   └── routes.py            # APIRouter: /tours
├── utils/
│   ├── __init__.py
│   ├── encryption.py        # Encriptación de datos
│   └── geo_utils.py         # Haversine: distancia + duración estimada
└── wallets/
    ├── __init__.py
    ├── controller.py        # balance, history, initialize (S2S), recharge (S2S)
    ├── model.py             # Pydantic model: WalletResponse, etc.
    └── routes.py            # APIRouter: /wallets
```

## Estructura de Archivos: Node.js → Python

```
NODE.JS (Server-Client)                    PYTHON (Server-ClientPY)
──────────────────────────────────         ─────────────────────────────────
server-client/index.js                     app/main.py
server-client/configs/app.js               app/configs/app.py
server-client/configs/db.js                app/configs/database.py
server-client/configs/cors-configuration.js CORSMiddleware
server-client/middlewares/auth-validators.js app/middlewares/validate_jwt.py
server-client/middlewares/validate-jwt.js   (dead code en Node → eliminado)
server-client/middlewares/wallet-validators.js app/middlewares/wallets_validators.py
server-client/middlewares/tour-validators.js app/middlewares/tours_validators.py
server-client/middlewares/check-validators.js (general validation)
server-client/middlewares/data-validators.js (general validation)
server-client/middlewares/handle-errors.js FastAPI exception handlers
server-client/src/profiles/profile.model.js app/profiles/model.py
server-client/src/profiles/profile.controller.js app/profiles/controller.py
server-client/src/profiles/profile.routes.js app/profiles/routes.py
server-client/src/tours/tour.model.js      app/tours/model.py
server-client/src/tours/tour.controller.js app/tours/controller.py
server-client/src/tours/tour.routes.js     app/tours/routes.py
server-client/src/wallets/wallet.model.js  app/wallets/model.py
server-client/src/wallets/wallet.controller.js app/wallets/controller.py
server-client/src/wallets/wallet.routes.js app/wallets/routes.py
server-client/src/utils/encrypt.js         app/utils/encryption.py
server-client/src/utils/geo-utils.js       app/utils/geo_utils.py
server-client/src/utils/jwt.js             (dead code en Node → eliminado)
```

## Mapeo de Módulos

### Database (MongoDB)
- `configs/db.js` (`mongoose.connect()`) → `app/configs/database.py` (`motor.AsyncIOMotorClient`)
- Database: `TransmetroUserDb`
- URI: `mongodb://localhost:27017/TransmetroUserDb`
- **Diferencia:** Server-ClientPY llama `load_dotenv()` a nivel de módulo en `main.py`

### JWT Verification
- Node.js: `middlewares/auth-validators.js` (extrae de `Authorization: Bearer`, verifica con `jsonwebtoken`, soporta claims Node y .NET)
- Python: `app/middlewares/validate_jwt.py` (PyJWT `jwt.decode()`, mismo soporte dual de claims)
- **Nota:** Server-Client usa **PyJWT** (no python-jose como Auth-Python)

```python
# Equivalente a auth-validators.js
import jwt

def verify_token(request: Request):
    auth = request.headers.get("authorization") or request.headers.get("token")
    if not auth:
        raise HTTPException(401, "Token inválido")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else auth
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido")
    return {"id": payload.get("sub") or payload.get("uid"), "role": payload.get("role")}
```

### S2S Endpoints (Server-to-Server)
- `x-internal-secret` header con `INTERNAL_SECRET`
- Endpoints: `POST /wallets/initialize`, `POST /wallets/recharge`
- Node.js: `middlewares/wallet-validators.js` verifica header
- Python: `app/middlewares/verify_internal_secret.py` con FastAPI `Depends()`

```python
# Equivalente a la verificación de internal secret
async def verify_internal_secret(request: Request):
    secret = request.headers.get("x-internal-secret")
    if secret != INTERNAL_SECRET:
        raise HTTPException(401, "Unauthorized: invalid internal secret")
```

### Wallets (Billetera Virtual)
- **GET /wallets/balance** — JWT required, retorna saldo actual
- **GET /wallets/history** — JWT required, retorna historial paginado (page/limit)
- **POST /wallets/initialize** — S2S (x-internal-secret), crea wallet para usuario
- **POST /wallets/recharge** — S2S, incrementa saldo

Pydantic models:
```python
class WalletResponse(BaseModel):
    id: str
    userId: str
    balance: float
    createdAt: datetime

class WalletInitializeBody(BaseModel):
    userId: str
    amount: float = 0.0

class WalletRechargeBody(BaseModel):
    userId: str
    amount: float = Field(gt=0)
```

### Tours (Planificación de Viajes)
- **GET /tours/history** — JWT required, historial de viajes del usuario
- **POST /tours/plan** — JWT required, planificar y pagar viaje

Lógica de tarifa (misma que Node.js):
- TRANSMETRO: Q1.00
- TUBUS: Q1.00
- TRANSURBANO: Q2.00
- Viajes de cortesía se decrementan antes del saldo

Pydantic models:
```python
class PlanTourBody(BaseModel):
    origin: list[float]      # [lng, lat]
    destination: list[float] # [lng, lat]
    systemType: str          # "TRANSMETRO" | "TUBUS" | "TRANSURBANO"

class TourResponse(BaseModel):
    id: str
    userId: str
    origin: list[float]
    destination: list[float]
    distance: float
    duration: float
    fare: float
    systemType: str
    createdAt: datetime
```

### Profiles (Perfiles)
- **GET /profiles/me** — JWT required, retorna perfil del usuario
- **PUT /profiles/me** — JWT required, actualiza perfil

### Geo Utils
- `src/utils/geo-utils.js` → `app/utils/geo_utils.py`
- Haversine: calcular distancia entre dos puntos [lng, lat]
- Estimar duración del viaje basado en distancia

## Variables de entorno

```
PORT=3002
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345
INTERNAL_SECRET=SuperSecretS2S_Transmetro2026
```

## Detalles Importantes

- **`load_dotenv()`** se llama a nivel de módulo en `main.py` (a diferencia de los demás servicios)
- **PyJWT** en vez de python-jose — librería distinta, mismo secreto
- **Dead code eliminado:** `src/utils/jwt.js` y `middlewares/validate-jwt.js` estaban comentados en Node.js
- **PORT default:** Código dice 3001 pero Dockerfile expone 3002 — usar 3002
- **S2S auth:** Solo `/wallets/initialize` y `/wallets/recharge` usan `x-internal-secret`
- **Pagination:** `page` y `limit` como query params, mismos defaults que Node.js
- **Fares hard-coded:** Tarifas por sistema de transporte en la lógica de tours
- **Sin Alembic:** MongoDB es schemaless
