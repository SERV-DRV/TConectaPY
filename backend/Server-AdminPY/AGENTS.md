# AGENTS.md — Tconecta Server Admin (Python)

## Descripción

Microservicio administrativo del sistema de tránsito Tconecta. API REST en Python con FastAPI, respaldada por MongoDB con soporte geoespacial (estaciones, rutas/carreteras, buses, alertas). Verifica tokens JWT emitidos por el servicio de autenticación.

## Comandos

```bash
# Instalar dependencias
pip install -e .

# Desarrollo (con recarga automática)
uvicorn app.main:app --reload --port 3001

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 3001

# Docker
docker compose up -d --build
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere MongoDB en ejecución (`TransmetroAdminDb`)
3. `JWT_SECRET` debe ser idéntico al configurado en el microservicio de autenticación
4. `AUTO_SEED=true` siembra datos automáticamente desde `app/data/transmetro.geojson`

## Arquitectura

- **FastAPI + Uvicorn** — Flujo asíncrono nativo (`async`/`await`)
- **Motor** — Driver asíncrono de MongoDB con indexación geoespacial (`2dsphere`)
- **Auto-seeder en Lifespan** — Si `stations` está vacío al arrancar, inserta datos semilla
- **Sin generación de JWT** — Solo verifica tokens del auth-server

## Base URL y Puerto

- **Base URL:** `/TCONECTA/v1`
- **Puerto:** 3001

## Estructura de módulos

```
app/
├── <entity>/
│   ├── model.py        # Modelo Pydantic
│   ├── controller.py   # Funciones handler (CRUD)
│   └── routes.py       # Router FastAPI
├── middlewares/
│   ├── validate_jwt.py       # Verificación JWT + admin role
│   └── *_validators.py       # Validadores Pydantic por módulo
├── configs/
│   ├── app.py          # Registro de rutas
│   └── database.py     # Conexión Motor
├── data/
│   └── transmetro.geojson
└── main.py             # Punto de entrada (lifespan)
```

## Auth & Authorization

- Endpoints mutantes (POST/PUT/PATCH): `validate_jwt` + `require_admin_role`
- Endpoints de lectura (GET): solo `validate_jwt`
- Excepción: `/buses` NO requiere auth (igual que en Node.js original)

## Variables de entorno

```
PORT=3001
MONGODB_URI=mongodb://localhost:27017/TransmetroAdminDb
JWT_SECRET=<mismo secret que auth-server>
AUTO_SEED=true
```
