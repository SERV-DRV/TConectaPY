import base64
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY
from app.auth_utils import decode_jwt, require_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Tconecta User Client", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="app/templates")


from app.routers import auth, planner, wallet, explore, alerts, profile

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(planner.router, prefix="/planner", tags=["Planner"])
app.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
app.include_router(explore.router, prefix="/explore", tags=["Explore"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])


@app.get("/")
async def root():
    return RedirectResponse("/planner")
