import httpx
from app.config import ADMIN_URL, AUTH_URL


async def admin_get(path: str, token: str = None, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.get(f"{ADMIN_URL}{path}", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()


async def admin_post(path: str, data: dict, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.post(f"{ADMIN_URL}{path}", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def admin_put(path: str, data: dict, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.put(f"{ADMIN_URL}{path}", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def admin_patch(path: str, data: dict, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.patch(f"{ADMIN_URL}{path}", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def admin_delete(path: str, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.delete(f"{ADMIN_URL}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def auth_get(path: str, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.get(f"{AUTH_URL}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def auth_post(path: str, data: dict, token: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.post(f"{AUTH_URL}{path}", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
