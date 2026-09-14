# Especificación de Traslado: Client-User (React → Python/FastAPI)

## Resumen

Conversión de la app de usuario Tconecta de React+Vite+Tailwind+Zustand a Python/FastAPI+Jinja2+HTMX+TailwindCSS(CDN). Conecta a 3 microservicios: Auth-Server (8080), Server-AdminPY (3001), Server-ClientPY (3002).

## Tecnología de Origen → Destino

| Componente | Original | Equivalente Python |
|---|---|---|
| Framework | React 19 + Vite | FastAPI + Jinja2 |
| Routing | React Router DOM v7 | FastAPI Router (server-side) |
| Estado global | Zustand (userAuthStore) | Sesiones FastAPI |
| HTTP client | Axios (3 instancias) | httpx (async, 3 clientes) |
| Formularios | React controlled forms | HTMX + HTML forms |
| Renderizado | React re-renders | HTMX swap |
| Mapas | react-leaflet (RoutePlanner) | Leaflet CDN + JS inline |
| Gráficas | Recharts (ProfilePage) | Chart.js CDN |
| Tarjeta visual | CSS 3D flip (WalletPage) | CSS inline en template |
| Estilos | Tailwind CSS v4 | Tailwind CSS v4 (CDN play) |

## Estructura de Archivos

```
REACT (original)                          PYTHON (nuevo)
─────────────────────────────────         ─────────────────────────────────
src/main.jsx                              app/main.py
src/App.jsx                               app/main.py (routes)
src/api/clientApi.js                      app/api_client.py (3 clientes)
src/api/userApi.js                        app/api_client.py
src/store/userAuthStore.js                Sesiones FastAPI
src/components/Navbar.jsx                 app/templates/base.html (nav)
src/components/Pagination.jsx             HTMX hx-get + query params
src/pages/AuthPage.jsx                    app/templates/auth/login.html
src/pages/RoutePlannerPage.jsx            app/templates/planner/index.html
src/pages/WalletPage.jsx                  app/templates/wallet/index.html
src/pages/ExplorePage.jsx                 app/templates/explore/index.html
src/pages/AlertsPage.jsx                  app/templates/alerts/index.html
src/pages/ProfilePage.jsx                 app/templates/profile/index.html
```

## Páginas y sus equivalencias

### AuthPage.jsx → auth/login.html
- Login: CUI + Password → `<form hx-post="/auth/login">`
- Register: CUI + Email + Password → `<form hx-post="/auth/register">`
- Toggle login/register con HTMX

### RoutePlannerPage.jsx → planner/index.html
La página más compleja (745 líneas React). Equivalente Python:
- Mapa Leaflet CDN con click events para origen/destino
- Búsqueda de direcciones con Nominatim (fetch JS)
- Cálculo de ruta inteligente con OSRM (fetch JS)
- Stations y roads se cargan desde Server-AdminPY vía HTMX
- Pago via POST a Server-ClientPY
- Todo el algoritmo de routing se mantiene en JavaScript inline

```html
<!-- Mapa -->
<div id="map" style="height: 500px;"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  // Algoritmo de ruta inteligente (del RoutePlannerPage.jsx original)
  // Se mantiene en JS del lado del cliente
  async function calculateSmartRoute(origin, destination) { ... }
</script>
```

### WalletPage.jsx → wallet/index.html
- 3 tabs: Recargar, Comprar Tarjeta, Historial
- Tarjeta visual CSS 3D flip → CSS inline
- Formulario de tarjeta con validación Luhn en JS
- HTMX para submits y paginación de historial

### ExplorePage.jsx → explore/index.html
- 2 tabs: Rutas y Estaciones
- Grid paginado con HTMX
- Cada tarjeta muestra código, nombre, tipo

### AlertsPage.jsx → alerts/index.html
- Tarjetas de alertas con badges por tipo
- Simple HTMX GET con polling opcional

### ProfilePage.jsx → profile/index.html
- Tab 1: Estadísticas con Chart.js (gasto/distance por día)
- Tab 2: Datos de usuario con edición de email inline
- HTMX para update email

## API Client (3 backends)

```python
import httpx

AUTH_URL = "http://localhost:8080/api"
ADMIN_URL = "http://localhost:3001/TCONECTA/v1"
CLIENT_URL = "http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1"

async def auth_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{AUTH_URL}{path}", headers=headers, **kwargs)
        return resp.json()

async def admin_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{ADMIN_URL}{path}", headers=headers, **kwargs)
        return resp.json()

async def client_request(method, path, token=None, **kwargs):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{CLIENT_URL}{path}", headers=headers, **kwargs)
        return resp.json()
```

## Sesiones

```python
# Login: guardar token y datos de usuario
request.session["token"] = data["token"]
request.session["user"] = {"id": user_id, "cui": cui, "role": role}

# Decoder JWT manual (de userAuthStore.js)
import base64, json
payload = json.loads(base64.b64decode(token.split(".")[1] + "=="))
user = {"id": payload["sub"], "cui": payload["cui"], "role": payload["role"]}
```

## Route Planner (el más complejo)

El planificador de rutas se mantiene principalmente en JavaScript del lado del cliente, igual que en React. La diferencia es que los templates se sirven desde FastAPI pero la lógica de mapa/rutas es JS puro:

1. Cargar estaciones y rutas activas (HTMX on page load)
2. Click en mapa → geocoding inverso (Nominatim JS)
3. Búsqueda de dirección → geocoding directo (Nominatim JS)
4. Calcular ruta inteligente (Haversine + OSRM, JS)
5. Pagar viaje → HTMX POST a `/planner/pay`

## Variables de entorno

```
SECRET_KEY=super-secret-key-for-sessions
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
CLIENT_URL=http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1
```
