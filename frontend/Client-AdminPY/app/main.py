import base64
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY


def decode_jwt(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        role = data.get("role") or data.get(
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role", "User"
        )
        return {"id": data.get("sub"), "cui": data.get("cui"), "role": role}
    except Exception:
        return {}


async def require_auth(request: Request):
    token = request.session.get("token")
    if not token:
        return RedirectResponse("/auth/login", status_code=302)
    user = decode_jwt(token)
    if not user:
        request.session.clear()
        return RedirectResponse("/auth/login", status_code=302)
    request.state.user = user
    request.state.token = token
    return user


async def require_admin(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    if user.get("role") != "Admin":
        return RedirectResponse("/auth/login", status_code=302)
    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Tconecta Admin Client", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="app/templates")


from app.routers import auth, dashboard, roads, stations, buses, alerts, users

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(roads.router, prefix="/roads", tags=["Roads"])
app.include_router(stations.router, prefix="/stations", tags=["Stations"])
app.include_router(buses.router, prefix="/buses", tags=["Buses"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(users.router, prefix="/users", tags=["Users"])


@app.get("/")
async def root():
    return RedirectResponse("/dashboard")
