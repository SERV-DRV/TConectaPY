import httpx
from app.config import AUTH_URL, ADMIN_URL, CLIENT_URL


async def auth_request(method: str, path: str, token: str = None, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{AUTH_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()


async def admin_request(method: str, path: str, token: str = None, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{ADMIN_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()


async def client_request(method: str, path: str, token: str = None, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{CLIENT_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()


# Invoice methods (call Auth-Server wallet endpoints)
async def get_invoice(invoice_id: str, token: str) -> dict:
    return await auth_request("GET", f"/wallets/invoice/{invoice_id}", token=token)


async def get_invoices(page: int = 1, limit: int = 10, token: str = None) -> dict:
    return await auth_request("GET", f"/wallets/invoices?page={page}&limit={limit}", token=token)
