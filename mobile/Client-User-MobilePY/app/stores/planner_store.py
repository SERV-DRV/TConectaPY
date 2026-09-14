import asyncio
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
            print(f"[EXPLORE] Roads response keys: {list(roads_data.keys()) if isinstance(roads_data, dict) else type(roads_data)}")
            print(f"[EXPLORE] Stations response keys: {list(stations_data.keys()) if isinstance(stations_data, dict) else type(stations_data)}")
            self.roads = roads_data.get("data", [])
            self.stations = stations_data.get("data", [])
            print(f"[EXPLORE] Roads: {len(self.roads)}, Stations: {len(self.stations)}")
        except Exception as ex:
            print(f"[EXPLORE ERROR] {ex}")
            self.roads = []
            self.stations = []
        finally:
            self.loading = False

    async def plan_trip(self, token: str, **kwargs):
        try:
            print(f"[PLANNER] plan_trip kwargs: {kwargs}")
            result = await client_request("POST", "/tours/plan", token=token, json=kwargs)
            print(f"[PLANNER] plan_trip result: {result}")
            await self.fetch_history(token)
            return True
        except Exception as ex:
            print(f"[PLANNER ERROR] plan_trip: {ex}")
            return False

    async def fetch_history(self, token: str):
        try:
            data = await client_request("GET", "/tours/history", token=token)
            self.history = data.get("data", []) if isinstance(data, dict) else data
        except Exception:
            self.history = []


planner_store = PlannerStore()
