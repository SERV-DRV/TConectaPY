# AGENTS.md — Tconecta Server Client (Python)

## Descripción

Microservicio de clientes del sistema de tránsito Tconecta. API REST en Python con FastAPI, respaldada por MongoDB. Gestiona billetera virtual, tours/viajes y perfiles de usuarios. Verifica tokens JWT del auth-server.

## Comandos

```bash
# Instalar dependencias
pip install -e .

# Desarrollo
uvicorn app.main:app --reload --port 3002

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 3002

# Docker
docker compose up -d --build
```

## Configuración del entorno

1. Copiar `.env.example` a `.env`
2. Requiere MongoDB en ejecución (`TransmetroUserDb`)
3. `JWT_SECRET` idéntico al auth-server
4. `INTERNAL_SECRET` para endpoints server-to-server

## Arquitectura

- **FastAPI + Uvicorn** — Flujo asíncrono nativo
- **Motor** — Driver asíncrono de MongoDB
- **Sin generación de JWT** — Solo verifica tokens

## Base URL y Puerto

- **Base URL:** `/TRANSMETRO-CONECTA-CLIENTE/v1`
- **Puerto:** 3002

## Estructura de módulos

```
app/
├── wallets/            # Billetera virtual (saldo, recargas, historial)
├── tours/              # Planificación y registro de viajes
├── profiles/           # Perfiles de usuario
├── middlewares/        # JWT, validadores
├── configs/            # App, database
└── main.py
```

## Variables de entorno

```
PORT=3002
MONGODB_URI=mongodb://localhost:27017/TransmetroUserDb
JWT_SECRET=<mismo secret que auth-server>
INTERNAL_SECRET=<para endpoints S2S>
```
