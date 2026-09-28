from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db, init_db
from app.database_mongo import connect_mongo, close_mongo, get_mongo_db
from app.models.seed import seed_database
from app.routers import auth, transaction, wallet, stripe


async def create_invoice_indexes():
    """Create MongoDB indexes for invoices collection."""
    try:
        mongo_db = get_mongo_db()
        await mongo_db.invoices.create_index([("userId", 1), ("fecha", -1)])
        print("[TransmetroAuth] Índices de facturas creados/verificados")
    except Exception as e:
        print(f"[TransmetroAuth] Error creando índices de facturas: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: init DBs + auto-seed al arrancar."""
    print("[TransmetroAuth] Iniciando servidor...")
    await init_db()
    await connect_mongo()
    await create_invoice_indexes()
    await seed_database()
    print(f"[TransmetroAuth] Servidor listo — puerto {settings.port}")
    yield
    await close_mongo()
    await close_db()
    print("[TransmetroAuth] Servidor detenido.")


app = FastAPI(
    title="TransmetroConecta Auth Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.node_env == "development" else None,
    redoc_url="/redoc" if settings.node_env == "development" else None,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-token", "x-internal-secret"],
)


# ── Global Exception Handler ────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    is_dev = settings.node_env == "development"
    status = getattr(exc, "status_code", 500)

    if isinstance(exc, ValueError):
        status = 400

    print(f"[TransmetroAuth] Error {status} en {request.method} {request.url.path}: {exc}")

    return JSONResponse(
        status_code=status,
        content={
            "StatusCode": status,
            "Message": str(exc) if status != 500 else "Error interno del servidor.",
            "Detailed": str(exc) if is_dev else None,
        },
    )


# ── Rutas ───────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/Auth", tags=["Auth"])
app.include_router(transaction.router, prefix="/api/transaction", tags=["Transaction"])
app.include_router(wallet.router, prefix="/api/wallets", tags=["Wallet"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["Stripe"])


@app.get("/api/health")
async def health():
    return {
        "status": "Healthy",
        "service": "TransmetroConecta Auth Python Service",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root():
    return {
        "success": True,
        "service": "TransmetroConecta Auth Python Service",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/Auth",
            "transaction": "/api/transaction",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
