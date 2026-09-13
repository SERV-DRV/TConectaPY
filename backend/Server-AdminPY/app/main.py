import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.configs.database import connect_db, close_db
from app.configs.app import create_app
from app.utils.auto_seeder import seed_transmetro_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    if os.getenv("AUTO_SEED", "false").lower() == "true":
        await seed_transmetro_data()
    yield
    await close_db()


app = create_app(lifespan=lifespan)
