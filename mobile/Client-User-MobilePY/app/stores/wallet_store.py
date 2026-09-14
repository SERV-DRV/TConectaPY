from app.api_client import auth_request


class WalletStore:
    def __init__(self):
        self.balance = 0.0
        self.loading = False
        self.last_message = ""

    async def fetch_balance(self, token: str):
        self.loading = True
        try:
            data = await auth_request("GET", "/wallets/balance", token=token)
            print(f"[WALLET] Balance raw: {data}")
            if isinstance(data, dict) and "balance" in data:
                self.balance = data["balance"]
            else:
                self.balance = data.get("data", {}).get("balance", 0)
        except Exception as ex:
            print(f"[WALLET ERROR] fetch_balance: {ex}")
        finally:
            self.loading = False

    async def recharge(self, token: str, card_number: str, exp: str, cvv: str, amount: float):
        try:
            result = await auth_request("POST", "/transaction/recharge", token=token, json={
                "cardNumber": card_number, "expirationDate": exp, "cvv": cvv, "amount": amount,
            })
            print(f"[WALLET] Recharge result: {result}")
            self.last_message = result.get("message", "")
            is_ok = result.get("isSuccess", False)
            if is_ok:
                import asyncio
                await asyncio.sleep(2)
                try:
                    await self.fetch_balance(token)
                except Exception:
                    pass
            return is_ok
        except Exception as ex:
            print(f"[WALLET ERROR] recharge: {ex}")
            self.last_message = str(ex)
            return False

    async def purchase_card(self, token: str, card_number: str, exp: str, cvv: str):
        try:
            result = await auth_request("POST", "/transaction/purchase-card", token=token, json={
                "cardNumber": card_number, "expirationDate": exp, "cvv": cvv, "amount": 20.00,
            })
            print(f"[WALLET] Purchase result: {result}")
            self.last_message = result.get("message", "")
            is_ok = result.get("isSuccess", False)
            if is_ok:
                import asyncio
                await asyncio.sleep(2)
                try:
                    await self.fetch_balance(token)
                except Exception:
                    pass
            return is_ok
        except Exception as ex:
            print(f"[WALLET ERROR] purchase_card: {ex}")
            self.last_message = str(ex)
            return False


wallet_store = WalletStore()
