# T-Conecta Ciudadano — Sistema de Tránsito Público Inteligente

Sistema completo de gestión de transporte público para la municipalidad. Incluye microservicios backend, aplicaciones web y app móvil ciudadana.

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTES                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Web Ciudadano │  │ Web Admin    │  │ App Móvil (APK)    │    │
│  │ (Flet/Jinja2) │  │ (Flet/Jinja2)│  │ (Flet → Flutter)   │    │
│  │   :5174       │  │   :5173      │  │  Android 5.0+      │    │
│  └──────┬────────┘  └──────┬───────┘  └────────┬───────────┘    │
│         │                 │                    │                │
├─────────┼─────────────────┼────────────────────┼────────────────┤
│         ▼                 ▼                    ▼                │
│                    MICROSERVICIOS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Auth Server  │  │ Admin Server │  │ Client Server      │     │
│  │ (FastAPI)    │  │ (FastAPI)    │  │ (FastAPI)          │     │
│  │   :8080      │  │   :3001      │  │   :3002            │     │
│  │ PostgreSQL   │  │ MongoDB      │  │ MongoDB            │     │
│  │ MongoDB      │  │ Transmetro   │  │ Transmetro         │     │
│  └──────┬───────┘  │ AdminDb      │  │ UserDb             │     │
│         │          └──────────────┘  └────────────────────┘     │
│         ▼                                                       │
│  ┌──────────────────┐                                           │
│  │ PostgreSQL 16    │                                           │
│  │ TransmetroAuthDb │                                           │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Servicios

| Servicio | Puerto | Tecnología | Base de Datos | Descripción |
|----------|--------|------------|---------------|-------------|
| Auth-Python | 8080 | FastAPI + SQLAlchemy + Motor | PostgreSQL + MongoDB | Autenticación, JWT, transacciones, billetera |
| Server-AdminPY | 3001 | FastAPI + Motor | MongoDB (TransmetroAdminDb) | CRUD de infraestructura: estaciones, rutas, buses, alertas |
| Server-ClientPY | 3002 | FastAPI + Motor | MongoDB (TransmetroUserDb) | Perfiles, tours/viajes, billetera del cliente |
| Client-UserPY | 5174 | FastAPI + Jinja2 | — | Web ciudadana (server-side rendered) |
| Client-AdminPY | 5173 | FastAPI + Jinja2 | — | Web administrativa (server-side rendered) |
| Mobile (APK) | — | Python Flet (Flutter) | SQLite local | App móvil Android con mapa |

## Modelo de Datos

### PostgreSQL — TransmetroAuthDb

**Tabla `transmetro_users`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID (PK) | Identificador único |
| cui | VARCHAR(13) UNIQUE | DPI del ciudadano (13 dígitos) |
| email | VARCHAR UNIQUE | Correo electrónico |
| password_hash | VARCHAR | bcrypt hash de la contraseña |
| role | VARCHAR | "User" o "Admin" |
| is_active | BOOLEAN | Estado de la cuenta |
| created_at | TIMESTAMP | Fecha de creación |

### MongoDB — TransmetroUserDb

**Colección `wallets`** (billetera virtual)

```json
{
  "_id": "user_uuid",
  "saldo": 125.00,
  "viajesCortesia": 5,
  "hasCitizenCard": true,
  "status": true,
  "isActive": true,
  "historialRecargas": [
    { "monto": 25.00, "fecha": "2026-09-14T05:00:00Z" }
  ],
  "created_at": "2026-09-14T00:00:00Z",
  "updated_at": "2026-09-14T05:00:00Z"
}
```

**Colección `tours`** (historial de viajes)

```json
{
  "_id": "uuid",
  "userId": "user_uuid",
  "origen": { "lat": 14.6375, "lon": -90.5195 },
  "destino": { "lat": 14.6259, "lon": -90.5109 },
  "distanciaMetros": 1588.75,
  "tiempoEstimadoMinutos": 14,
  "tarifaCobrada": 1.00,
  "systemType": "TRANSMETRO",
  "itinerary": "1. Camina hacia Estación San Agustín...",
  "originName": "Origen",
  "destName": "Destino",
  "status": true,
  "isActive": true,
  "created_at": "2026-09-14T05:48:08Z"
}
```

**Colección `profiles`** (perfiles de usuario)

```json
{
  "_id": "user_uuid",
  "fullName": "Juan Pérez",
  "preferredLanguage": "es",
  "frequentRoutes": []
}
```

### MongoDB — TransmetroAdminDb

**Colección `stations`**

```json
{
  "_id": "ObjectId",
  "name": "El Rodeo",
  "stationCode": "EST-012",
  "typeStation": "CENTRALES",
  "status": "ACTIVE",
  "location": {
    "type": "Point",
    "coordinates": [-90.560831, 14.6248]
  },
  "isActive": true
}
```

Tipos de estación: `CENTRALES`, `CARRIL LATERAL`, `TRASBORDO`, `TERMINALES`
Estados: `ACTIVE`, `INACTIVE`, `MAINTENANCE`, `CLOSED`

**Colección `roads`**

```json
{
  "_id": "ObjectId",
  "name": "Simeón a Cañas",
  "routeCode": "RUT-178",
  "typeRoad": "CENTRALES",
  "color": "#3388ff",
  "stations": ["station_id_1", "station_id_2"],
  "path": {
    "type": "LineString",
    "coordinates": [[-90.50, 14.62], [-90.51, 14.63]]
  },
  "status": "ACTIVE",
  "isActive": true
}
```

Tipos de ruta: `EXPRESS`, `RELEVOS`, `CENTRALES`

**Colección `buses`**

```json
{
  "_id": "ObjectId",
  "busNumber": "BUS-001",
  "licensePlate": "U1234ABC",
  "capacity": 60,
  "status": "ACTIVE",
  "assignedRoad": "road_id"
}
```

Formato de placa guatemalteca: `[UCP]` + 3-4 dígitos + 3 letras
- **U**: Urbano
- **C**: Comercial
- **P**: Público

**Colección `alerts`**

```json
{
  "_id": "ObjectId",
  "title": "Incidente en ruta 12",
  "description": "Accidente vehicular bloquea carril...",
  "typeAlert": "INCIDENT",
  "status": "ACTIVE"
}
```

Tipos: `INCIDENT`, `MAINTENANCE`, `INFO`

---

## Algoritmos Clave

### Algoritmo de Luhn (Validación de Tarjetas)

Utilizado para validar números de tarjetas de crédito/débito antes de procesar pagos.

**Ubicaciones**: `backend/Auth-Python/app/helpers/luhn.py`, `mobile/app/utils/luhn.py`

```python
def is_valid_luhn(card_number: str) -> bool:
    """
    Algoritmo de Luhn (Modulo 10):
    1. Eliminar espacios y guiones, verificar que solo contenga dígitos
    2. Verificar longitud mínima de 13 dígitos
    3. Tomar la posición de cada dígito desde la derecha:
       - Posiciones impares (desde derecha): sumar directamente
       - Posiciones pares (desde derecha): multiplicar × 2
         - Si el resultado > 9, sumar los dígitos individuales (ej: 14 → 1+4 = 5)
    4. Si la suma total % 10 == 0, la tarjeta es válida

    Ejemplo con tarjeta 4111111111111111:
    Dígitos: 4 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    Desde derecha, posiciones pares (×2):
      1×2=2, 1×2=2, 1×2=2, 1×2=2, 1×2=2, 1×2=2, 1×2=2, 1×2=2
    Suma: (1+1+1+1+1+1+1+1) + (2+2+2+2+2+2+2+2) = 8 + 16 = 24
    Con dígitos de 24: 2+4 = 6... ajuste: suma = 36 → 36 % 10 = 0 ✓
    """
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13:
        return False

    odd_digits = digits[-1::-2]    # Posiciones impares desde derecha
    even_digits = digits[-2::-2]   # Posiciones pares desde derecha

    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))  # Dividir en decenas y unidades

    return total % 10 == 0
```

**Flujo de uso en `transaction_service.py`**:
```
Usuario ingresa datos de tarjeta
  → Luhn valida el número de tarjeta
    → Si es inválido: retorna error 400 "Número de tarjeta inválido"
    → Si es válido: simula delay de pasarela de pago (1.5s)
      → Llama a wallet_integration.add_funds() para acreditar saldo
      → Retorna transactionId y mensaje de éxito
```

### Distancia de Haversine (Cálculo de Distancia entre Coordenadas)

Calcula la distancia geodésica entre dos puntos sobre la superficie de la Tierra.

**Backend** (`Server-ClientPY/app/utils/geo_utils.py`) — retorna metros:
```python
import math

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Fórmula de Haversine:
    a = sin²(Δφ/2) + cos(φ1) · cos(φ2) · sin²(Δλ/2)
    c = 2 · atan2(√a, √(1−a))
    d = R · c

    Donde:
      φ = latitud (radianes)
      λ = longitud (radianes)
      R = 6,371,000 metros (radio medio de la Tierra)

    Retorna distancia en METROS.
    """
    R = 6_371_000  # Radio de la Tierra en metros

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # metros
```

**Móvil** (`mobile/app/utils/haversine.py`) — retorna km:
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    # Misma fórmula, retorna distancia en KM
    ...

def estimate_duration_minutes(distance_km, speed_kmh=25):
    """Estima duración del viaje en minutos (velocidad promedio: 25 km/h)"""
    return math.ceil(distance_km / speed_kmh * 60)
```

**Velocidad de referencia**: 25 km/h (416.67 m/min) — promedio de autobús urbano en Guatemala.

### Sistema de Tarifas y Viajes de Cortesía

**Cálculo de tarifa** (`Server-ClientPY/app/tours/controller.py`):

```python
FARES = {
    "TRANSMETRO": 1.00,    # Q1.00 por viaje
    "TUBUS": 1.00,         # Q1.00 por viaje
    "TRANSURBANO": 2.00,   # Q2.00 por viaje
}

async def plan_tour(user_id, body):
    wallet = await db.wallets.find_one({"_id": user_id})

    # 1. Primero usar viajes de cortesía (tarjeta ciudadana)
    courtesy_left = wallet.get("viajesCortesia", 0)
    if courtesy_left > 0:
        new_courtesy = courtesy_left - 1
        used_courtesy = True
        fare = 0.0  # Gratis con cortesía
    else:
        # 2. Si no hay cortesía, descontar del saldo
        if wallet["saldo"] < fare:
            raise HTTPException(402, "Saldo insuficiente")
        new_balance = wallet["saldo"] - fare

    # 3. Registrar tour en MongoDB
    # 4. Actualizar saldo en wallet
```

### JWT (JSON Web Tokens)

El sistema usa JWT para autenticación stateless. Hay tres implementaciones:

**Generación** (Auth-Python, `python-jose`):
```python
def generate_access_token(user_id, cui, role):
    payload = {
        "sub": user_id,          # ID del usuario
        "cui": cui,              # DPI del ciudadano
        "role": role,            # "User" o "Admin"
        # Compatibilidad con .NET (backend existente):
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role": role,
        "iss": "TransmetroAuthServer",
        "aud": "TransmetroUsers",
        "exp": datetime.utcnow() + timedelta(minutes=120),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```

**Estructura de un JWT:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.     ← Header (algoritmo)
eyJzdWIiOiI2YWE3M2EyMWEzNGFl...             ← Payload (claims)
.3dwhr_fZ2ylMUalkN1W-Sm2QG10w...            ← Firma HMAC-SHA256
```

**Claims del payload:**
- `sub`: ID del usuario (UUID)
- `cui`: Número de DPI (13 dígitos)
- `role`: Rol del usuario ("User" / "Admin")
- `iss`: Emisor del token ("TransmetroAuthServer")
- `aud`: Audiencia ("TransmetroUsers")
- `exp`: Fecha de expiración (120 minutos)
- `iat`: Fecha de emisión

**Decodificación en cliente** (móvil/web — sin verificación):
```python
def decode_jwt(token):
    payload = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)  # Padding base64
    data = json.loads(base64.b64decode(payload))
    return {
        "id": data.get("sub"),
        "cui": data.get("cui"),
        "role": data.get("role"),
    }
```

### Geocoding (Nominatim — Solo Móvil)

Convierte direcciones/texto a coordenadas GPS usando OpenStreetMap.

```
GET https://nominatim.openstreetmap.org/search?q=Guatemala+Zona+10&countrycodes=gt&format=json&limit=1

Respuesta:
[{
  "lat": "14.5892",
  "lon": "-90.5087",
  "display_name": "Zona 10, Guatemala"
}]
```

User-Agent requerido: `TConectaApp/1.0`

### Cálculo de Ruta (OSRM — Solo Móvil)

Calcula la ruta óptima en carretera entre dos puntos usando OpenStreetMap.

```
GET https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?geometries=geojson

Respuesta:
{
  "routes": [{
    "geometry": { "coordinates": [[lon, lat], ...], "type": "LineString" },
    "distance": 1588.75,  // metros
    "duration": 856.3     // segundos
  }]
}
```

La polyline resultante se renderiza en el mapa con `PolylineMarker` de Flet.

### Generación de Itinerario (Móvil)

Al calcular una ruta, el sistema genera instrucciones paso a paso:

```python
# 1. Buscar estación más cercana al origen (distancia euclidiana)
nearest_orig = min(stations, key=lambda s: station_dist(s, origin))

# 2. Buscar estación más cercana al destino
nearest_dest = min(stations, key=lambda s: station_dist(s, dest))

# 3. Generar itinerario
if nearest_orig == nearest_dest:
    itinerary = f"""1. Camina hacia Estación {nearest_orig.name}.
2. Toma ruta con transbordo hacia troncales.
3. Baja en Estación {nearest_dest.name}.
4. Camina hacia tu destino."""
else:
    itinerary = f"""1. Camina hacia Estación {nearest_orig.name}.
2. Aborda Ruta {road.name}.
3. Baja en Estación {nearest_dest.name}.
4. Camina hacia tu destino."""
```

---

## API Endpoints

### Auth Server (puerto 8080)

#### Autenticación — `/api/Auth`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/register` | Registrar ciudadano | No |
| `POST` | `/login` | Iniciar sesión | No |
| `POST` | `/recover-password` | Solicitar recuperación | No |
| `POST` | `/reset-password` | Restablecer contraseña | No |
| `GET` | `/users` | Listar usuarios | Admin |
| `POST` | `/register-admin` | Registrar admin | Admin |
| `GET` | `/me/email` | Obtener email propio | JWT |
| `PUT` | `/update-email` | Actualizar email | JWT |

**Login — Request:**
```json
{
  "cui": "2000000000002",
  "password": "Usuario123!"
}
```

**Login — Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "userId": "f536dcef-74b4-4e09-a94f-d2f29837ae97",
  "role": "User"
}
```

**Register — Request:**
```json
{
  "cui": "2000000000003",
  "email": "ciudadano@test.com",
  "password": "MiPassword123!"
}
```

#### Transacciones — `/api/transaction`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/recharge` | Recargar billetera | JWT |
| `POST` | `/purchase-card` | Comprar tarjeta ciudadana (Q20) | JWT |

**Recharge — Request:**
```json
{
  "cardNumber": "4111111111111111",
  "expirationDate": "12/28",
  "cvv": "123",
  "amount": 25.00
}
```

**Recharge — Response:**
```json
{
  "isSuccess": true,
  "message": "Recarga procesada exitosamente.",
  "transactionId": "de9e0762-365b-4b1e-96c6-27223df81966"
}
```

#### Billetera — `/api/wallets`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/balance` | Consultar saldo | JWT |

**Balance — Response:**
```json
{
  "balance": 125.00,
  "courtesyTrips": 5,
  "hasCitizenCard": true
}
```

### Admin Server (puerto 3001)

Base URL: `/TCONECTA/v1`

#### Estaciones — `/stations`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/` | Listar (paginado) | JWT |
| `GET` | `/all` | Todas las estaciones | JWT |
| `GET` | `/{id}` | Detalle de estación | JWT |
| `POST` | `/` | Crear estación | Admin |
| `PUT` | `/{id}` | Actualizar estación | Admin |
| `PUT` | `/{id}/status` | Cambiar estado | Admin |

**Crear Estación — Request:**
```json
{
  "name": "El Rodeo",
  "stationCode": "EST-012",
  "typeStation": "CENTRALES",
  "coordinates": [-90.560831, 14.6248]
}
```

#### Rutas — `/roads`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/` | Listar (paginado) | JWT |
| `GET` | `/all` | Todas las rutas | JWT |
| `GET` | `/{id}` | Detalle de ruta | JWT |
| `POST` | `/` | Crear ruta | Admin |
| `PUT` | `/{id}` | Actualizar ruta | Admin |
| `PUT` | `/{id}/status` | Cambiar estado | Admin |

**Crear Ruta — Request:**
```json
{
  "name": "Simeón a Cañas",
  "routeCode": "RUT-178",
  "typeRoad": "CENTRALES",
  "color": "#3388ff",
  "stations": ["EST-012", "EST-015"],
  "coordinates": [[-90.5608, 14.6248], [-90.5195, 14.6375]]
}
```

#### Buses — `/buses`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/` | Listar buses | JWT |
| `GET` | `/{id}` | Detalle de bus | JWT |
| `POST` | `/` | Crear bus | Admin |
| `PUT` | `/{id}` | Actualizar bus | Admin |
| `PATCH` | `/{id}/status` | Cambiar estado | Admin |

**Crear Bus — Request:**
```json
{
  "busNumber": "BUS-001",
  "licensePlate": "U1234ABC",
  "capacity": 60,
  "assignedRoad": "route_id_opcional"
}
```

**Validación de placa**: `^[UCP]\d{3,4}[A-Z]{3}$` — formato guatemalteco.

#### Alertas — `/alerts`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/` | Alertas activas | JWT |
| `POST` | `/` | Crear alerta | Admin |
| `PUT` | `/{id}/status` | Resolver alerta | Admin |
| `DELETE` | `/{id}` | Eliminar alerta | Admin |

**Crear Alerta — Request:**
```json
{
  "title": "Incidente en Ruta 12",
  "description": "Accidente vehicular bloquea carril izquierdo",
  "typeAlert": "INCIDENT"
}
```

### Client Server (puerto 3002)

Base URL: `/TRANSMETRO-CONECTA-CLIENTE/v1`

#### Perfiles — `/profiles`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/me` | Obtener perfil | JWT |
| `PUT` | `/me` | Actualizar perfil | JWT |

#### Tours/Viajes — `/tours`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/history` | Historial de viajes | JWT |
| `POST` | `/plan` | Planificar y pagar viaje | JWT |

**Plan Tour — Request:**
```json
{
  "originLat": 14.6375,
  "originLon": -90.5195,
  "destLat": 14.6259,
  "destLon": -90.5109,
  "systemType": "TRANSMETRO",
  "itinerary": "1. Camina hacia Estación San Agustín..."
}
```

**Plan Tour — Response:**
```json
{
  "tourId": "4acb9a4a-2212-4e39-b76b-b265a77935f5",
  "systemType": "TRANSMETRO",
  "estimatedDistance": "1588.75 m",
  "estimatedTime": "14 min",
  "chargedFare": "Q1.00",
  "remainingBalance": "Q124.00",
  "courtesyTripsLeft": 4,
  "itinerary": "1. Camina hacia Estación San Agustín..."
}
```

#### Billetera — `/wallets`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/balance` | Consultar saldo | JWT |
| `GET` | `/history` | Historial de recargas | JWT |
| `POST` | `/initialize` | Inicializar billetera | S2S |
| `POST` | `/recharge` | Recargar (server-to-server) | S2S |

---

## Desarrollo Local

### Requisitos previos

- Python 3.11+
- PostgreSQL 16+
- MongoDB 6.0+
- Docker + Docker Compose (recomendado)

### Iniciar todo con Docker

```bash
cd backend/Auth-Python
docker compose up --build
```

Esto levanta los 7 servicios:
- PostgreSQL: `localhost:5432`
- MongoDB: `localhost:27017`
- Auth Server: `localhost:8080`
- Admin Server: `localhost:3001`
- Client Server: `localhost:3002`
- Web Admin: `localhost:5173`
- Web Ciudadano: `localhost:5174`

### Desarrollo sin Docker

```bash
# Auth Server
cd backend/Auth-Python
cp .env.example .env  # Editar variables
pip install -e .
uvicorn app.main:app --reload --port 8080

# Admin Server
cd backend/Server-AdminPY
pip install -e .
uvicorn app.main:app --reload --port 3001

# Client Server
cd backend/Server-ClientPY
pip install -e .
uvicorn app.main:app --reload --port 3002

# Web Ciudadano
cd frontend/Client-UserPY
pip install -e .
uvicorn app.main:app --reload --port 5174

# Web Admin
cd frontend/Client-AdminPY
pip install -e .
uvicorn app.main:app --reload --port 5173
```

### Variables de Entorno

**Auth Server** (`.env`):
```
PORT=8080
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/TransmetroAuthDb
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
JWT_SECRET=tu_secreto_aqui
JWT_AUDIENCE=TransmetroUsers
JWT_ISSUER=TransmetroAuthServer
JWT_EXPIRATION_MINUTES=120
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

**Client Server** (`.env`):
```
PORT=3002
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
JWT_SECRET=tu_secreto_aqui
INTERNAL_SECRET=secreto_s2s
```

**Admin Server** (`.env`):
```
PORT=3001
MONGODB_URI=mongodb://localhost:27017/TransmetroAdminDb
JWT_SECRET=tu_secreto_aqui
AUTO_SEED=true
```

**Web Ciudadano/Mobile** (`.env`):
```
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
```

### Credenciales de Prueba

| CUI | Contraseña | Rol |
|-----|------------|-----|
| `2000000000001` | `Admin123!` | Admin |
| `2000000000002` | `Usuario123!` | User |
| `2000000000003` | `Admin123!` | Admin |

---

## App Móvil — Flet (Python → Flutter)

### Tecnología

La app móvil usa **Flet** (https://flet.dev), un framework que compila Python a Flutter nativo. No es un wrapper web — genera APK nativo con rendimiento real.

### Pantallas

| Pantalla | Descripción |
|----------|-------------|
| Login | CUI + contraseña, persistencia de sesión en SQLite |
| Registro | CUI + email + contraseña con validación |
| Planificador | Mapa interactivo (OpenStreetMap), tap para seleccionar origen/destino, cálculo de ruta OSRM, itinerario paso a paso, pago de viaje |
| Billetera | Saldo con gradiente visual, tabs recarga/comprar tarjeta, validación Luhn |
| Explorar | Tabs rutas/estaciones con scroll, cards con información |
| Alertas | Lista de alertas activas con badges de color por tipo |
| Perfil | CUI, rol, estado, cerrar sesión |

### Navegación

```python
# NavigationBar con 5 tabs (cache de pantallas)
NavigationBar(
    destinations=[
        NavigationBarDestination(icon=MAP, label="Planificador"),
        NavigationBarDestination(icon=CREDIT_CARD, label="Billetera"),
        NavigationBarDestination(icon=BUS_ALERT, label="Explorar"),
        NavigationBarDestination(icon=WARNING, label="Alertas"),
        NavigationBarDestination(icon=PERSON, label="Perfil"),
    ],
)
```

Las pantallas se cachean y se refrescan al cambiar de tab.

### Persistencia Local (SQLite)

```sql
CREATE TABLE auth (
    key TEXT PRIMARY KEY,
    value TEXT
);
-- Almacena: token JWT, datos del usuario
```

### Construcción del APK

**Prerrequisitos**: Docker instalado

```bash
cd mobile/Client-User-MobilePY

# Build con Docker (recomendado)
docker compose up --build

# El APK se genera en:
# bin/tconecta-1.0.0-arm64-v8a-debug.apk
```

**buildozer.spec**:
```ini
[app]
title = T-Conecta Ciudadano
package.name = tconecta
package.domain = com.tconecta
version = 1.0.0
requirements = python3,flet,flet-map,httpx,python-jose[cryptography]
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
```

### Permisos Android

- `INTERNET` — Comunicación con backend
- `ACCESS_FINE_LOCATION` — GPS para ubicación actual
- `ACCESS_COARSE_LOCATION` — Ubicación aproximada

---

## CI/CD — GitHub Actions

Archivo: `.github/workflows/playwright-tests.yml`

**Triggers**:
- Push a `main` o `develop`
- Pull request a `main`
- Manual dispatch

**Steps**:
1. Checkout del código
2. Python 3.11 + cache de Buildozer
3. Dependencias del sistema (JDK 17, build tools)
4. `buildozer android debug`
5. Upload del APK como artifact (30 días de retención)
6. Crear GitHub Release en push de tag

---

## Despliegue en Render

### URLs de Producción

| Servicio | URL |
|----------|-----|
| Auth Server | `https://tconecta-auth.onrender.com/api` |
| Admin Server | `https://tconecta-admin.onrender.com/TCONECTA/v1` |
| Client Server | `https://tconecta-client.onrender.com/TRANSMETRO-CONECTA-CLIENTE/v1` |
| Web Ciudadano | `https://tconecta-client.onrender.com/` |
| Web Admin | `https://tconecta-admin.onrender.com/` |

### Variables de Entorno en Render

Las apps móviles y web detectan automáticamente el entorno:

```python
# config.py — Auto-detección
def is_local_backend():
    """Detecta si el backend corre en local (puerto 8080 ocupado)"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 8080))
        s.close()
        return result == 0
    except:
        return False
```

En producción, usa automáticamente las URLs de Render.

---

## Estructura de Directorios

```
TConectaPY/
├── .github/workflows/playwright-tests.yml    # CI/CD para APK
├── README.md                       # Este archivo
├── spec_trasladoaPython.md         # Especificación de migración
│
├── backend/
│   ├── Auth-Python/                # Servicio de autenticación
│   │   ├── app/
│   │   │   ├── main.py             # FastAPI app + lifespan
│   │   │   ├── config.py           # Pydantic Settings
│   │   │   ├── database.py         # SQLAlchemy (PostgreSQL)
│   │   │   ├── database_mongo.py   # Motor (MongoDB)
│   │   │   ├── helpers/
│   │   │   │   ├── jwt.py          # JWT encode/decode
│   │   │   │   ├── luhn.py         # Algoritmo de Luhn
│   │   │   │   └── password.py     # bcrypt hash/verify
│   │   │   ├── middlewares/
│   │   │   │   ├── validate_jwt.py # JWT middleware
│   │   │   │   ├── require_admin.py# Admin role guard
│   │   │   │   └── request_limit.py# Rate limiting
│   │   │   ├── models/
│   │   │   │   ├── user.py         # SQLAlchemy User model
│   │   │   │   └── seed.py         # Auto-seed users
│   │   │   ├── routers/
│   │   │   │   ├── auth.py         # /api/Auth/*
│   │   │   │   ├── transaction.py  # /api/transaction/*
│   │   │   │   └── wallet.py       # /api/wallets/*
│   │   │   ├── schemas/
│   │   │   │   └── auth.py         # Pydantic schemas
│   │   │   └── services/
│   │   │       ├── auth_service.py         # Lógica de auth
│   │   │       ├── transaction_service.py  # Pagos + Luhn
│   │   │       └── wallet_integration.py   # MongoDB wallets
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── Server-AdminPY/             # Servicio admin
│   │   └── app/
│   │       ├── stations/           # CRUD estaciones
│   │       ├── roads/              # CRUD rutas
│   │       ├── buses/              # CRUD buses
│   │       ├── alerts/             # CRUD alertas
│   │       ├── data/
│   │       │   └── transmetro.geojson  # Datos reales Transmetro
│   │       └── utils/
│   │           └── auto_seeder.py  # Seed desde GeoJSON
│   │
│   └── Server-ClientPY/            # Servicio cliente
│       └── app/
│           ├── profiles/           # Perfiles de usuario
│           ├── tours/              # Planificación + pago viajes
│           ├── wallets/            # Billetera virtual
│           └── utils/
│               └── geo_utils.py    # Haversine + estimación tiempo
│
├── frontend/
│   ├── Client-UserPY/              # Web ciudadana
│   │   └── app/
│   │       ├── routers/            # auth, planner, wallet, explore, alerts, profile
│   │       └── templates/          # Jinja2 HTML templates
│   │
│   └── Client-AdminPY/             # Web admin
│       └── app/
│           ├── routers/            # auth, dashboard, roads, stations, buses, alerts, users
│           └── templates/          # Jinja2 HTML templates
│
└── mobile/
    └── Client-User-MobilePY/       # App móvil Android
        ├── app/
        │   ├── main.py             # Entry point Flet
        │   ├── navigation.py       # NavigationBar + screen cache
        │   ├── config.py           # URLs de backend
        │   ├── api_client.py       # httpx client (3 backends)
        │   ├── screens/            # 7 pantallas
        │   ├── stores/             # 4 state managers
        │   └── utils/              # luhn, haversine, storage
        ├── buildozer.spec          # Config Android APK
        ├── Dockerfile              # Ubuntu 22.04 + Buildozer
        └── docker-compose.yml      # Build automation
```

---

## Testing — Playwright E2E

### Requisitos

```bash
pip install playwright pytest pytest-html
playwright install chromium
```

### Estructura de tests

```
test/
├── conftest.py                 # Fixtures (login_admin, login_user) con retry
├── test_admin_login.py         # Login administrador
├── test_admin_dashboard.py     # Dashboard stats
├── test_admin_buses.py         # CRUD buses (create + edit + status)
├── test_admin_roads.py         # CRUD rutas (status + edit modal + create modal)
├── test_admin_stations.py      # CRUD estaciones (status + edit modal + create modal)
├── test_admin_alerts.py        # CRUD alertas (create + resolve)
├── test_admin_users.py         # Crear admin
├── test_user_login.py          # Login ciudadano
├── test_user_planner.py        # Planificador (mapa + inputs + historial)
├── test_user_wallet.py         # Billetera (recarga + compra tarjeta + historial)
├── test_user_explore.py        # Explorar rutas/estaciones
├── test_user_alerts.py         # Ver alertas
└── test_user_profile.py        # Perfil (ver + tabs)
```

### Comandos

```bash
# Correr todos los tests
pytest test/ -v

# Ver el navegador ejecutando los tests
pytest test/ -v --headed

# Generar reporte HTML
pytest test/ -v --html=report.html

# Correr un test específico
pytest test/test_admin_buses.py -v

# Parar en el primer error
pytest test/ -v -x

# Correr solo tests de admin
pytest test/ -v -k "admin"

# Correr solo tests de user
pytest test/ -v -k "user"
```

### Credenciales de test

| CUI | Contraseña | Rol | Páginas |
|-----|------------|-----|---------|
| `1000000000001` | `Admin123!` | Admin | Dashboard, Roads, Stations, Buses, Alerts, Users |
| `2000000000002` | `Usuario123!` | User | Planner, Wallet, Explore, Alerts, Profile |

### Screenshots y Videos

Los tests generan automáticamente screenshots y videos cuando fallan (configurado en `pyproject.toml`):

```toml
[tool.pytest.ini_options]
addopts = "--screenshot=only-on-failure --video=retain-on-failure --output=test-results"
```

Los archivos se guardan en `test-results/` (excluido del `.gitignore`).

### Rate Limiting

El auth server tiene rate limiting (429 Too Many Requests). El fixture `conftest.py` incluye un retry automático (3 intentos con 5 segundos de espera) para manejar esto.

---

## Licencia

Proyecto Privado.
