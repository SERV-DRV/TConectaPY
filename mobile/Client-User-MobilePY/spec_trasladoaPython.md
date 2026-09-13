# Especificación de Traslado: Client-User-Mobile (React Native/Expo → Python/Flet)

## Resumen

Conversión de la app móvil ciudadana Tconecta de React Native + Expo a Python + Flet (basado en Flutter). Flet permite crear apps móviles nativas con Python que compilan a Android, iOS, web y desktop.

## Tecnología de Origen → Destino

| Componente | Original | Equivalente Python |
|---|---|---|
| Framework móvil | React Native 0.83 + Expo ~55 | Flet (Flutter backend) |
| Navegación | React Navigation v7 (Stack + Tabs) | flet.RouteInformationParser +-tabs |
| Estado global | Zustand + AsyncStorage | Clases Python + SQLite |
| HTTP client | Axios | httpx (async) |
| Mapas | react-native-maps (Google Maps) | flet-google-maps o flutter_map |
| Charts | react-native-chart-kit | fl_chart (via Flet) |
| Icons | Lucide React Native | flet.Icon con Icons de Flutter |
| Storage | AsyncStorage | SQLite via sqlite3 |
| Geolocalización | expo-location | geolocator (Python) |
| Animaciones | React Native Animated | flet.AnimatedSwitcher |
| Build | EAS (Expo) | Buildozer (Python→APK) |

## Estructura de Archivos: React Native → Python

```
REACT NATIVE (original)                PYTHON/FLET (nuevo)
─────────────────────────────          ─────────────────────────────
App.jsx                               app/main.py
src/navigation/AppNavigator.jsx        app/navigation/router.py
src/navigation/AuthStack.jsx           app/screens/login.py, register.py
src/navigation/MainTabs.jsx            app/navigation/router.py (tabs)
src/shared/api/apiClient.js            app/api_client.py
src/shared/api/index.js                app/api_client.py
src/shared/store/authStore.py          app/stores/auth_store.py
src/shared/store/walletStore.py        app/stores/wallet_store.py
src/shared/store/plannerStore.py       app/stores/planner_store.py
src/shared/store/alertsStore.py        app/stores/alerts_store.py
src/shared/utils/haversine.py          app/utils/haversine.py
src/shared/utils/luhn.py              app/utils/luhn.py
src/shared/constants/endpoints.py      app/config.py
src/shared/components/Button.py        flet.ElevatedButton
src/shared/components/Input.py         flet.TextField
src/features/auth/screens/LoginScreen    app/screens/login.py
src/features/auth/screens/RegisterScreen app/screens/register.py
src/features/planner/screens/PlannerScreen app/screens/planner.py
src/features/wallet/screens/WalletScreen   app/screens/wallet.py
src/features/explore/screens/ExploreScreen app/screens/explore.py
src/features/alerts/screens/AlertsScreen    app/screens/alerts.py
src/features/profile/screens/ProfileScreen  app/screens/profile.py
```

## Patrones de Navegación

### React Navigation → Flet
```python
# React Navigation: <Navigator> con conditional rendering
# Flet: RouteInformationParser con.pages

class AppRouter:
    def __init__(self, page: ft.Page):
        self.page = page

    def build(self):
        if not auth_store.isAuthenticated:
            return ft.View("/login", [LoginScreen(self.page)])
        return ft.View("/", [
            ft.NavigationBar(
                destinations=[
                    ft.NavigationBarDestination(icon="map", text="Planificador"),
                    ft.NavigationBarDestination(icon="credit_card", text="Billetera"),
                    ft.NavigationBarDestination(icon="bus", text="Explorar"),
                    ft.NavigationBarDestination(icon="warning", text="Alertas"),
                    ft.NavigationBarDestination(icon="person", text="Perfil"),
                ],
                on_change=self.on_tab_change,
            ),
        ])
```

## Zustand Stores → Python Classes

```python
# Original: Zustand store con persist
# Python: Clase con SQLite para persistencia

class AuthStore:
    def __init__(self):
        self.user = None
        self.token = None
        self.is_authenticated = False

    async def login(self, cui, password):
        data = await auth_request("POST", "/Auth/login", data={"cui": cui, "password": password})
        self.token = data["token"]
        self.user = decode_jwt(self.token)
        self.is_authenticated = True
        save_to_storage("token", self.token)

    def logout(self):
        self.token = None
        self.user = None
        self.is_authenticated = False
        clear_storage()
```

## API Client (httpx)

```python
import httpx

AUTH_URL = "http://localhost:8080/api"
ADMIN_URL = "http://localhost:3001/TCONECTA/v1"
CLIENT_URL = "http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1"

async def auth_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{AUTH_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

async def admin_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{ADMIN_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

async def client_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{CLIENT_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()
```

## Mapas en Flet

Flet usa `flet_google_maps` o `flutter_map` como widget de mapa:

```python
import flet_google_maps as gmaps

map_view = gmaps.GoogleMapView(
    api_key=GOOGLE_MAPS_API_KEY,
    initial_camera_position=gmaps.CameraPosition(
        target=gmaps.LatLng(14.62, -90.52),
        zoom=13,
    ),
    markers=[gmaps.Marker(position=gmaps.LatLng(14.62, -90.52))],
    polylines=[gmaps.Polyline(points=[...], color="blue", width=4)],
)
```

## Tarjeta 3D Animada

```python
# React Native: Animated API con Y-axis rotation
# Flet: AnimatedSwitcher con rotación

class Card3D(ft.Container):
    def __init__(self):
        super().__init__()
        self.front = self.build_front()
        self.back = self.build_back()
        self.showing_front = True
        self.content = self.front

    def flip(self):
        self.showing_front = not self.showing_front
        self.content = self.front if self.showing_front else self.back
        self.update()
```

## Persistencia Local (SQLite)

```python
import sqlite3

def init_db():
    conn = sqlite3.connect("tconecta.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS auth (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def save_to_storage(key, value):
    conn = sqlite3.connect("tconecta.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO auth (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_from_storage(key):
    conn = sqlite3.connect("tconecta.db")
    c = conn.cursor()
    c.execute("SELECT value FROM auth WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
```

## Buildozer (Android APK)

```ini
# buildozer.spec
[app]
title = T-Conecta
package.name = tconecta
package.domain = com.tconecta
source.dir = app
source.include_exts = py,png,jpg,kv,atlas,ttf
requirements = python3,flet,httpx
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
```

## Variables de entorno

```
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
USER_URL=http://localhost:3003/TRANSMETRO-CONECTA-USUARIO/v1
GOOGLE_MAPS_API_KEY=<tu_api_key>
```
