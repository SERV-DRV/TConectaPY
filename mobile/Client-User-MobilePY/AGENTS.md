# AGENTS.md — Tconecta Client User Mobile (Python)

## Descripción

Aplicación móvil ciudadana del sistema de tránsito Tconecta. Construida con Python usando **Flet** (basado en Flutter) para UI nativa multiplataforma. Conecta a 3 microservicios: Auth-Python (8080), Server-Admin (3001), Server-Client (3002). Permite planificar viajes con mapa, gestionar billetera virtual, explorar infraestructura y ver alertas.

## Comandos

```bash
# Instalar dependencias
pip install -e .

# Desarrollo (desktop)
flet run app/main.py

# Build Android APK (requiere Buildozer)
buildozer android debug

# Build iOS (requiere Xcode)
flet build ios
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere los 4 microservicios ejecutándose
3. Buildozer para builds Android/iOS

## Arquitectura

- **Flet** — Framework Python basado en Flutter para UI nativa
- **httpx** — Cliente HTTP async para 4 microservicios
- **Zustand-like pattern** — State management con clases Python
- **JWT** — Verificación de tokens del auth-server

## APIs a las que conecta

### Auth-Server (`http://localhost:8080/api`)
- `POST /Auth/login` — Login
- `POST /Auth/register` — Registro
- `POST /Transaction/recharge` — Recargar billetera
- `POST /Transaction/purchase-card` — Comprar tarjeta

### Server-Admin (`http://localhost:3001/TCONECTA/v1`)
- `GET /alerts` — Alertas de servicio
- `GET /roads/all?status=ACTIVE` — Rutas activas
- `GET /stations/all?status=ACTIVE` — Estaciones activas

### Server-Client (`http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1`)
- `GET /wallets/balance` — Saldo billetera
- `GET /tours/history` — Historial viajes
- `POST /tours/plan` — Pagar y registrar viaje

## Estructura

```
app/
├── main.py              # Punto de entrada Flet
├── config.py            # URLs de backends, API keys
├── api_client.py        # Cliente httpx para 4 microservicios
├── navigation/
│   └── router.py        # Navegación entre pantallas
├── screens/
│   ├── login.py         # Login/CUI
│   ├── register.py      # Registro
│   ├── planner.py       # Planificador con mapa
│   ├── wallet.py        # Billetera + tarjeta 3D
│   ├── explore.py       # Explorar rutas/estaciones
│   ├── alerts.py        # Alertas de servicio
│   └── profile.py       # Perfil + estadísticas
├── stores/
│   ├── auth_store.py    # Estado de autenticación
│   ├── wallet_store.py  # Estado de billetera
│   ├── planner_store.py # Estado de planificación
│   └── alerts_store.py  # Estado de alertas
├── widgets/
│   ├── card_3d.py       # Tarjeta de crédito animada
│   ├── map_view.py      # Componente de mapa
│   └── alert_badge.py   # Badge de tipo de alerta
└── utils/
    ├── haversine.py     # Distancia + duración estimada
    ├── luhn.py          # Validación de tarjetas
    └── storage.py       # Persistencia local (SQLite)
```

## Variables de entorno

```
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
```
