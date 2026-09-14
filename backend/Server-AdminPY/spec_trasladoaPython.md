# Especificación de Traslado: Server-Admin (Node.js) → Server-AdminPY (FastAPI)

## Resumen

Conversión del microservicio administrativo de Node.js/Express 5/Mongoose/MongoDB a Python/FastAPI/Motor/MongoDB. API REST con soporte geoespacial (2dsphere) para estaciones, rutas/carreteras, buses y alertas. Verifica JWTs sin generarlos.

## Tecnología de Origen → Destino

| Componente | Original (Node.js) | Equivalente Python |
|---|---|---|
| Framework | Express 5 | FastAPI |
| MongoDB ODM | Mongoose 9 (sync/async) | Motor 3.6 (async nativo) |
| Validación body | express-validator / hand-rolled | Pydantic models |
| JWT verification | jsonwebtoken + `validate-jwt.js` | python-jose + `Depends(validate_jwt)` |
| Middleware auth | `validateJWT` + `requireAdminRole` | `Depends(validate_jwt)` + `Depends(require_admin_role)` |
| Swagger docs | swagger-ui-express (manually defined) | FastAPI `/docs` (auto-generated desde Pydantic) |
| Auto-seeder | `src/utils/auto-seeder.js` (GeoJSON) | `app/utils/auto_seeder.py` (GeoJSON) |
| Geospatial indexes | Mongoose `2dsphere` | Motor `create_index([("location", "2dsphere")])` |
| Rate limiting | express-rate-limit | No implementado (pendiente) |
| Env vars | dotenv + `process.env` | pydantic-settings (`BaseSettings`) |
| HTTP client | axios | httpx |
| CORS | cors middleware | CORSMiddleware |
| Logger | morgan | print() / logging |
| Error handler | `handle-errors.js` | `@app.exception_handler` o FastAPI HTTPException |

## `__init__.py` — Estructura de Paquetes

```
app/
├── __init__.py              # Vacío
├── main.py                  # FastAPI app + lifespan (connect_db + auto_seed)
├── alerts/
│   ├── __init__.py
│   ├── controller.py        # CRUD handlers: get_all, create, update, resolve, delete
│   ├── model.py             # Pydantic model: AlertCreate, AlertUpdate, AlertResponse
│   └── routes.py            # APIRouter: /alerts
├── buses/
│   ├── __init__.py
│   ├── controller.py
│   ├── model.py
│   └── routes.py            # APIRouter: /buses (sin auth)
├── configs/
│   ├── __init__.py
│   ├── app.py               # create_app: registra routers + CORS
│   ├── database.py          # Motor: connect_db, get_db, close_db
│   └── swagger.py           # Config Swagger (opcional, FastAPI auto-genera)
├── data/
│   └── transmetro.geojson   # Datos semilla: estaciones, rutas
├── middlewares/
│   ├── __init__.py
│   ├── alerts_validators.py # Pydantic validators para alerts
│   ├── buses_validators.py  # Pydantic validators para buses
│   ├── roads_validators.py  # Pydantic validators para roads
│   ├── stations_validators.py
│   └── validate_jwt.py      # Depends: JWT verification + admin role
├── roads/
│   ├── __init__.py
│   ├── controller.py        # CRUD + geoespacial: near, within
│   ├── model.py
│   └── routes.py            # APIRouter: /roads
├── stations/
│   ├── __init__.py
│   ├── controller.py        # CRUD + geoespacial
│   ├── model.py
│   └── routes.py            # APIRouter: /stations
└── utils/
    ├── __init__.py
    └── auto_seeder.py       # Seed desde transmetro.geojson
```

## Estructura de Archivos: Node.js → Python

```
NODE.JS (Server-Admin)                     PYTHON (Server-AdminPY)
──────────────────────────────────         ─────────────────────────────────
server-admin/index.js                      app/main.py
server-admin/configs/app.js                app/configs/app.py (create_app)
server-admin/configs/db.js                 app/configs/database.py (Motor)
server-admin/configs/cors-configuration.js CORSMiddleware
server-admin/configs/swagger.js            FastAPI auto-docs (/docs)
server-admin/configs/helmet-configuration.js No necesario
server-admin/middlewares/validate-jwt.py   app/middlewares/validate_jwt.py
server-admin/middlewares/auth-validators.js app/middlewares/validate_jwt.py
server-admin/middlewares/alerts-validators.js app/middlewares/alerts_validators.py
server-admin/middlewares/buses-validators.js  app/middlewares/buses_validators.py
server-admin/middlewares/roads-validators.js  app/middlewares/roads_validators.py
server-admin/middlewares/stations-validators.py app/middlewares/stations_validators.py
server-admin/middlewares/request-limit.js  (pendiente)
server-admin/middlewares/handle-errors.js  @app.exception_handler
server-admin/src/alerts/alert.model.js     app/alerts/model.py
server-admin/src/alerts/alert.controller.js app/alerts/controller.py
server-admin/src/alerts/alert.routes.js    app/alerts/routes.py
server-admin/src/buses/bus.model.js        app/buses/model.py
server-admin/src/buses/bus.controller.js   app/buses/controller.py
server-admin/src/buses/bus.routes.js       app/buses/routes.py
server-admin/src/roads/road.model.js       app/roads/model.py
server-admin/src/roads/road.controller.js  app/roads/controller.py
server-admin/src/roads/road.routes.js      app/roads/routes.py
server-admin/src/stations/station.model.js app/stations/model.py
server-admin/src/stations/station.controller.js app/stations/controller.py
server-admin/src/stations/station.routes.js app/stations/routes.py
server-admin/src/utils/auto-seeder.js      app/utils/auto_seeder.py
server-admin/src/data/transmetro.geojson   app/data/transmetro.geojson
```

## Mapeo de Módulos

### Database (MongoDB)
- `configs/db.js` (`mongoose.connect()`) → `app/configs/database.py` (`motor.motor_asyncio.AsyncIOMotorClient`)
- Mismo database: `TransmetroAdminDb`
- Mismo URI: `mongodb://localhost:27017/TransmetroAdminDb`

### Modelos (Mongoose → Pydantic)
Mongoose schema:
```js
const roadSchema = new Schema({
  name: { type: String, required: true },
  code: { type: String, required: true, unique: true },
  path: { type: [[Number]], required: true }, // GeoJSON LineString
  status: { type: String, enum: ['ACTIVE', 'INACTIVE'], default: 'ACTIVE' },
}, { timestamps: { createdAt: 'createdAt', updatedAt: 'updatedAt' } });
```

Pydantic equivalente:
```python
class RoadCreate(BaseModel):
    name: str
    code: str
    path: list[list[float]]  # [[lng, lat], ...]
    status: str = "ACTIVE"

class RoadResponse(BaseModel):
    id: str
    name: str
    code: str
    path: list[list[float]]
    status: str
    createdAt: datetime
    updatedAt: datetime
```

En `controller.py`, las queries se hacen con Motor:
```python
# Equivalente a Road.find({ status: 'ACTIVE' })
cursor = db.roads.find({"status": "ACTIVE"})
roads = await cursor.to_list(length=None)
```

### Geoespacial
- Mongoose: `roadSchema.index({ path: '2dsphere' })` → Motor: `await db.roads.create_index([("path", "2dsphere")])`
- Mongoose: `Station.find({ location: { $near: { $geometry: ..., $maxDistance: ... } } })` → Motor: `db.stations.find({"location": {"$near": {"$geometry": ..., "$maxDistance": ...}}})`
- Formato GeoJSON: `[longitude, latitude]` (no lat/lng)

### Auth & Authorization
- `middlewares/validate-jwt.js` → `app/middlewares/validate_jwt.py` con FastAPI `Depends()`
- `middlewares/require-admin-role.js` → `app/middlewares/require_admin_role.py` con FastAPI `Depends()`
- Patrón: endpoints mutantes usan `Depends(validate_jwt)` + `Depends(require_admin_role)`
- Excepción: `/buses` NO requiere auth (mismo comportamiento que Node.js)

### Auto-seeder
- `src/utils/auto-seeder.js` (lee `transmetro.geojson`, inserta si colecciones vacías) → `app/utils/auto_seeder.py` (misma lógica con Motor)
- Trigger: `AUTO_SEED=true` en env + colecciones vacías
- Datos: estaciones con `location` (GeoJSON Point), rutas con `path` (GeoJSON LineString)

### Rutas
- Express Router → FastAPI `APIRouter`
- `app.use(\`${BASE_URL}/roads\`, roadRoutes)` → `app.include_router(road_router, prefix="/TCONECTA/v1/roads")`
- Base URL: `/TCONECTA/v1`

### Validadores Pydantic (equivalente a middlewares/*-validators.js)
```python
# Equivalente a roads-validators.js
class RoadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    path: list[list[float]] = Field(..., min_length=2)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")
```

## Variables de entorno

```
PORT=3001
MONGODB_URI=mongodb://localhost:27017/TransmetroAdminDb
JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345
AUTO_SEED=true
```

## Detalles Importantes

- **Sin generación de JWT** — Solo verifica tokens del auth-server
- **`/buses` sin auth** — Intencional, mismo comportamiento que Node.js
- **2dsphere indexes** — Se crean en `connect_db()` al iniciar
- **Formato coordenadas** — GeoJSON `[lng, lat]`, no `[lat, lng]`
- **Swagger auto** — FastAPI genera docs desde Pydantic models (no necesita `swagger-ui-express`)
- **Timestamps manuales** — `created_at` y `updated_at` se establecen en el controller, no por el ORM
- **Sin Alembic** — MongoDB es schemaless, no hay migraciones
