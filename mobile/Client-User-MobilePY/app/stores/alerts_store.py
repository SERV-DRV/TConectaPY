from app.api_client import admin_request


class AlertsStore:
    def __init__(self):
        self.alerts = []
        self.loading = False

    async def fetch_alerts(self, token: str):
        self.loading = True
        try:
            data = await admin_request("GET", "/alerts", token=token)
            self.alerts = data.get("data", [])
        except Exception:
            self.alerts = []
        finally:
            self.loading = False


alerts_store = AlertsStore()
