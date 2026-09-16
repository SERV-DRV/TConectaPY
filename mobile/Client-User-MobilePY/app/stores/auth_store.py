from app.utils.storage import get, save, clear, decode_jwt, init_db
from app.api_client import auth_request
import json


class AuthStore:
    def __init__(self):
        self.user = None
        self.token = None
        self.is_authenticated = False
        self.loading = False

    def init_auth(self):
        init_db()
        token = get("token")
        if token:
            self.token = token
            self.user = decode_jwt(token)
            if not self.user:
                self.token = None
                self.is_authenticated = False
                clear()
                return
            import time
            exp = self.user.get("exp")
            if exp and exp < time.time():
                self.token = None
                self.user = None
                self.is_authenticated = False
                clear()
                return
            self.is_authenticated = True

    async def login(self, cui: str, password: str):
        self.loading = True
        try:
            data = await auth_request("POST", "/Auth/login", json={"cui": cui, "password": password})
            token = data.get("token") or data.get("accessToken")
            if token:
                self.token = token
                self.user = decode_jwt(token)
                self.is_authenticated = True
                save("token", token)
                return True
            return False
        except Exception as ex:
            print(f"[AUTH ERROR] {ex}")
            return False
        finally:
            self.loading = False

    async def register(self, cui: str, email: str, password: str):
        self.loading = True
        try:
            data = await auth_request("POST", "/Auth/register", json={"cui": cui, "email": email, "password": password})
            token = data.get("token") or data.get("accessToken")
            if token:
                self.token = token
                self.user = decode_jwt(token)
                self.is_authenticated = True
                save("token", token)
                return True
            return False
        except Exception as ex:
            print(f"[AUTH ERROR] {ex}")
            return False
        finally:
            self.loading = False

    def logout(self):
        self.token = None
        self.user = None
        self.is_authenticated = False
        clear()


auth_store = AuthStore()
