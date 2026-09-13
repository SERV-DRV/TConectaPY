import base64
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
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
    request.state.toast_msg = request.session.pop("toast_msg", None)
    request.state.toast_error = request.session.pop("toast_error", None)
    return user


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
