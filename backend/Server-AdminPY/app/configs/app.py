from typing import Optional
from contextlib import AbstractAsyncContextManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs import swagger as swagger_config
from app.stations.routes import router as station_routes
from app.roads.routes import router as road_routes
from app.alerts.routes import router as alert_routes
from app.buses.routes import router as bus_routes

BASE_URL = "/TCONECTA/v1"


def create_app(lifespan: Optional[AbstractAsyncContextManager] = None) -> FastAPI:
    app = FastAPI(
        title=swagger_config.TITLE,
        description=swagger_config.DESCRIPTION,
        version=swagger_config.VERSION,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(road_routes, prefix=BASE_URL)
    app.include_router(station_routes, prefix=BASE_URL)
    app.include_router(alert_routes, prefix=BASE_URL)
    app.include_router(bus_routes, prefix=BASE_URL)

    @app.get(f"{BASE_URL}/health")
    async def health_check():
        return {"status": "ok", "service": "TRANSMETRO-CONECTA Admin", "version": "1.0.0"}

    return app
