from app.api_client import client_request, auth_request


class WalletStore:
    def __init__(self):
        self.balance = 0.0
        self.loading = False

    async def fetch_balance(self, token: str):
        self.loading = True
        try:
            data = await client_request("GET", "/wallets/balance", token=token)
            self.balance = data.get("data", {}).get("balance", 0)
        except Exception:
            self.balance = 0
        finally:
            self.loading = False

    async def recharge(self, token: str, card_number: str, exp: str, cvv: str, amount: float):
        try:
            await auth_request("POST", "/Transaction/recharge", data={
                "cardNumber": card_number, "expirationDate": exp, "cvv": cvv, "amount": amount,
            })
            await self.fetch_balance(token)
            return True
        except Exception:
            return False

    async def purchase_card(self, token: str, card_number: str, exp: str, cvv: str):
        try:
            await auth_request("POST", "/Transaction/purchase-card", data={
                "cardNumber": card_number, "expirationDate": exp, "cvv": cvv, "amount": 20.00,
            })
            await self.fetch_balance(token)
            return True
        except Exception:
            return False


wallet_store = WalletStore()
