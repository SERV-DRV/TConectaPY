# Especificación de Traslado: Client-User-Mobile (React Native/Expo) → Client-User-MobilePY (Flet)

## Resumen

Conversión de la aplicación móvil ciudadana de React Native 0.83/Expo 55/Zustand a Python/Flet (basado en Flutter). La app conecta a 3 microservicios: Auth-Python (8080), Server-AdminPY (3001), Server-ClientPY (3002). Permite planificar viajes con mapa, gestionar billetera virtual, explorar infraestructura y ver alertas.

## Tecnología de Origen → Destino

| Componente | Original (React Native) | Equivalente Python |
|---|---|---|
| Framework UI | React Native 0.83 + Expo 55 | Flet 0.25+ (Flutter-based) |
| Navigation | @react-navigation/native (Stack + Tabs) | Flet `NavigationBar` + `page.views` |
| State management | Zustand 5 (create + hooks) | Python classes con state manual |
| Persistent storage | @react-native-async-storage/async-storage | SQLite local (`utils/storage.py`) |
| HTTP client | Axios (interceptor + instances) | httpx (async) |
| Maps | react-native-maps | flet-map (map widget) |
| JWT decode | jwt-decode (npm) | python-jose + base64 decode |
| Icons | @expo/vector-icons | `ft.Icons.*` (Material Icons nativos) |
| Safe area | react-native-safe-area-context | Flet maneja esto nativamente |
| Status bar | expo-status-bar | `page.window` config |
| Luhn validation | src/shared/utils/luhn.js | app/utils/luhn.py |
| Haversine | src/shared/utils/haversine.js | app/utils/haversine.py |
| Build APK | EAS Build / Buildozer | Buildozer (`buildozer.spec`) |
| Hot reload | Expo Go / Metro | `flet run --reload` |

## `__init__.py` — Estructura de Paquetes

```
app/
├── __init__.py              # Vacío
├── main.py                  # Punto de entrada Flet (ft.run(main))
├── config.py                # URLs de backends desde env vars
├── api_client.py            # httpx.AsyncClient para Auth + Server-Admin + Server-Client
├── navigation/
│   ├── __init__.py          # Exporta show_login, show_main
│   └── router.py            # AppRouter: login ↔ main (NavigationBar con 5 tabs)
├── screens/
│   ├── __pycache__/
│   ├── alerts.py            # Alertas de servicio (tarjetas con badges)
│   ├── explore.py           # Explorar rutas/estaciones (grid)
│   ├── login.py             # Login/CUI input
│   ├── planner.py           # Planificador con mapa (flet-map)
│   ├── profile.py           # Perfil (CUI, rol, logout — sin email edit)
│   ├── register.py          # Registro (CUI + email + password)
│   └── wallet.py            # Billetera + tarjeta 3D (tabs: Recargar/Historial)
├── stores/
│   ├── __pycache__/
│   ├── alerts_store.py      # Estado de alertas (lista + loading)
│   ├── auth_store.py        # Estado de auth (token, user, is_authenticated)
│   ├── planner_store.py     # Estado de planificación (origin, destination, route)
│   └── wallet_store.py      # Estado de billetera (balance, history)
└── utils/
    ├── __pycache__/
    ├── haversine.py         # Distancia + duración estimada entre coordenadas
    ├── luhn.py              # Validación de número de tarjeta
    ├── storage.py           # SQLite: save, get, clear, decode_jwt, init_db
    └── ui_helpers.py        # Funciones reutilizables de UI Flet
```

## Estructura de Archivos: React Native → Python

```
REACT NATIVE (original)                    PYTHON (nuevo)
──────────────────────────────────         ─────────────────────────────────
App.jsx                                    app/main.py
index.js (registerRootComponent)           ft.run(main)
src/navigation/AppNavigator.jsx            app/main.py (check auth → show_login/show_main)
src/navigation/AuthStack.jsx               app/navigation/router.py (build_screen "login")
src/navigation/MainTabs.jsx               app/navigation/router.py (NavigationBar 5 tabs)
src/shared/api/apiClient.js                app/api_client.py (httpx async)
src/shared/api/index.js                    app/api_client.py
src/shared/constants/endpoints.js          app/config.py (BaseSettings)
src/shared/store/authStore.js              app/stores/auth_store.py (AuthStore class)
src/shared/store/walletStore.js            app/stores/wallet_store.py
src/shared/store/plannerStore.js           app/stores/planner_store.py
src/shared/store/alertsStore.js            app/stores/alerts_store.py
src/shared/utils/haversine.js              app/utils/haversine.py
src/shared/utils/luhn.js                   app/utils/luhn.py
src/shared/components/Button.jsx           ft.ElevatedButton / ft.FilledButton
src/shared/components/Input.jsx            ft.TextField
src/features/auth/screens/LoginScreen.jsx  app/screens/login.py
src/features/auth/screens/RegisterScreen.jsx app/screens/register.py
src/features/planner/screens/PlannerScreen.jsx app/screens/planner.py
src/features/wallet/screens/WalletScreen.jsx app/screens/wallet.py
src/features/explore/screens/ExploreScreen.jsx app/screens/explore.py
src/features/alerts/screens/AlertsScreen.jsx app/screens/alerts.py
src/features/profile/screens/ProfileScreen.jsx app/screens/profile.py
```

## Mapeo de Componentes

### Navigation
- React Navigation: `createNativeStackNavigator` + `createBottomTabNavigator` → Flet: `page.views` + `ft.NavigationBar`
- `AppNavigator.jsx` (check `isAuthenticated`) → `app/main.py` (check `auth_store.is_authenticated`)
- `AuthStack` (Login → Register) → `router.py` `build_screen("login")`
- `MainTabs` (5 tabs) → `router.py` `NavigationBar` con 5 destinos

```python
# Equivalente a MainTabs.jsx
ft.NavigationBar(
    destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.MAP, text="Planificador"),
        ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, text="Billetera"),
        ft.NavigationBarDestination(icon=ft.Icons.BUS_ALERT, text="Explorar"),
        ft.NavigationBarDestination(icon=ft.Icons.WARNING, text="Alertas"),
        ft.NavigationBarDestination(icon=ft.Icons.PERSON, text="Perfil"),
    ],
    on_change=lambda e: self._on_tab_change(e.control.selected_index),
)
```

### Auth Store (Zustand → Python class)
- `create((set, get) => ({...}))` → `class AuthStore` con atributos `self.token`, `self.user`, `self.is_authenticated`
- `AsyncStorage.getItem/setItem/removeItem` → `app/utils/storage.py` (SQLite: `save()`, `get()`, `clear()`)
- `set({ token, user, isAuthenticated })` → `self.token = token; self.is_authenticated = True`

```python
# Equivalente a authStore.js
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
            self.is_authenticated = bool(self.user)

    async def login(self, cui: str, password: str):
        data = await auth_request("POST", "/Auth/login", json={"cui": cui, "password": password})
        token = data.get("token")
        if token:
            self.token = token
            self.user = decode_jwt(token)
            self.is_authenticated = True
            save("token", token)
            return True
        return False

auth_store = AuthStore()  # Singleton global
```

### API Client
- Axios instances (3 clientes con baseURL diferentes) → httpx.AsyncClient con functions
- Interceptor de token → se agrega `Authorization` header en cada request

```python
# Equivalente a clientApi.js (3 instancias axios)
import httpx

AUTH_URL = "http://localhost:8080/api"
ADMIN_URL = "http://localhost:3001/TCONECTA/v1"
CLIENT_URL = "http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1"

async def auth_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{AUTH_URL}{path}", headers=headers, **kwargs)
        return resp.json()
```

### Screens (JSX → Flet widgets)
- React Native components → Flet equivalents:
  - `<View>` → `ft.Column` / `ft.Container`
  - `<Text>` → `ft.Text`
  - `<TextInput>` → `ft.TextField`
  - `<TouchableOpacity>` → `ft.GestureDetector` / `ft.ElevatedButton`
  - `<Image>` → `ft.Image`
  - `<FlatList>` → `ft.ListView` / `ft.Column` con `ft.ListView`
  - `<ScrollView>` → `ft.ListView`
  - `<Modal>` → `ft.BottomSheet` / `ft.AlertDialog`

### Wallet Screen
- React Native: 3 tabs con state → Flet: `ft.Tabs` con `ft.Tab`
- CSS 3D flip card → Flet: `ft.AnimatedSwitcher` o CSS inline via `ft.Html`
- Tabs: Recargar, Comprar Tarjeta, Historial

### Planner Screen
- react-native-maps → flet-map (`ft.Map` con markers y polylines)
- Click events para seleccionar origen/destino
- Nominatim geocoding vía httpx
- OSRM routing vía httpx

### Persistent Storage
- `AsyncStorage.setItem('tconecta_mobile_token', token)` → SQLite:
  ```python
  save("token", token)  # INSERT OR REPLACE INTO kv_store
  ```
- `AsyncStorage.getItem('tconecta_mobile_token')` → `get("token")`
- `decode_jwt()` decodifica payload sin verificación (confía en auth-server)

## Variables de entorno

```
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
GOOGLE_MAPS_API_KEY=<key para flet-map tiles>
```

## Build & Deploy

| Acción | React Native | Flet |
|---|---|---|
| Dev desktop | `npx expo start` | `flet run app/main.py` |
| Build APK | `eas build -p android` | `buildozer android debug` |
| Build iOS | `eas build -p ios` | `flet build ios` (requiere Xcode) |
| Config build | `eas.json` | `buildozer.spec` |
| Icon | `app.json` → `icon` | `assets/icon.png` + `buildozer.spec` |

## Detalles Importantes

- **Sin email edit:** `ProfileScreen` en mobile NO tiene edición de email (a diferencia de Client-User web)
- **SQLite local:** Token se persiste en SQLite (`tconecta.db`), no en AsyncStorage
- **Singleton stores:** `auth_store = AuthStore()` es un singleton global (no hay React re-renders)
- **Flet es sync/async:** Las screens usan `async def` para httpx calls pero Flet UI es sync
- **Navigation manual:** `page.views.clear()` + `page.views.append()` + `page.update()` (no hay router declarativo)
- **Sin hot module replacement:** Flet tiene `--reload` pero no es HMR como Expo
- **Window size:** Se configura manualmente en `main.py` (`page.window.width/height`)
- **Buildozer:** Requiere Linux o WSL para build de APK
- **`GOOGLE_MAPS_API_KEY`** se necesita para tiles del mapa en planner
