from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.configs.app import register_routes
from app.configs.database import connect_db, close_db

load_dotenv()


@asynccontextmanager
async def lifespan(application: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Server-Client PY",
    description="Microservicio de operaciones para usuarios finales - Transmetro Conecta",
    version="1.0.0",
    lifespan=lifespan,
)

register_routes(app)


@app.get("/TRANSMETRO-CONECTA-CLIENTE/v1/health")
async def health_check():
    return {"status": "ok", "service": "server-client-py", "version": "1.0.0"}
