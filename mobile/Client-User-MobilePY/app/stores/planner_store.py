from app.api_client import admin_request, client_request


class PlannerStore:
    def __init__(self):
        self.roads = []
        self.stations = []
        self.history = []
        self.loading = False

    async def fetch_map_data(self, token: str):
        self.loading = True
        try:
            roads_data, stations_data = await asyncio.gather(
                admin_request("GET", "/roads/all?status=ACTIVE", token=token),
                admin_request("GET", "/stations/all?status=ACTIVE", token=token),
            )
            self.roads = roads_data.get("data", [])
            self.stations = stations_data.get("data", [])
        except Exception:
            self.roads = []
            self.stations = []
        finally:
            self.loading = False

    async def plan_trip(self, token: str, **kwargs):
        try:
            await client_request("POST", "/tours/plan", token=token, json=kwargs)
            await self.fetch_history(token)
            return True
        except Exception:
            return False

    async def fetch_history(self, token: str):
        try:
            data = await client_request("GET", "/tours/history", token=token)
            self.history = data.get("data", []) if isinstance(data, dict) else data
        except Exception:
            self.history = []


import asyncio

planner_store = PlannerStore()
