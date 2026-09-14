import httpx
from app.config import AUTH_URL, ADMIN_URL, CLIENT_URL


async def auth_request(method: str, path: str, token: str = None, json: dict = None, **kwargs) -> dict:
    url = f"{AUTH_URL}{path}"
    print(f"[API] {method} {url}")
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, url, headers=headers, json=json)
        print(f"[API] Status: {resp.status_code}")
        print(f"[API] Body: {resp.text[:500]}")
        resp.raise_for_status()
        return resp.json()


async def admin_request(method: str, path: str, token: str = None, json: dict = None, **kwargs) -> dict:
    url = f"{ADMIN_URL}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, url, headers=headers, json=json)
        resp.raise_for_status()
        return resp.json()


async def client_request(method: str, path: str, token: str = None, json: dict = None, **kwargs) -> dict:
    url = f"{CLIENT_URL}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, url, headers=headers, json=json)
        resp.raise_for_status()
        return resp.json()
