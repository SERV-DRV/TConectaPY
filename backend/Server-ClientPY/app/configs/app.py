from fastapi import FastAPI

from app.profiles.routes import router as profiles_router
from app.tours.routes import router as tours_router
from app.wallets.routes import router as wallets_router

BASE_URL = "/TRANSMETRO-CONECTA-CLIENTE/v1"


def register_routes(app: FastAPI):
    app.include_router(profiles_router, prefix=f"{BASE_URL}/profiles", tags=["Profiles"])
    app.include_router(tours_router, prefix=f"{BASE_URL}/tours", tags=["Tours"])
    app.include_router(wallets_router, prefix=f"{BASE_URL}/wallets", tags=["Wallets"])
