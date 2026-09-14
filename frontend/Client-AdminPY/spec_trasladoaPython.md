# Especificación de Traslado: Client-Admin (React → Python/FastAPI)

## Resumen

Conversión del panel de administración Tconecta de React+Vite+Tailwind+Zustand a Python/FastAPI+Jinja2+HTMX+TailwindCSS(CDN). El cliente se comunica con Server-AdminPY (puerto 3001) y Auth-Server (puerto 8080).

## Tecnología de Origen (Node.js/React)

| Componente | Original | Equivalente Python |
|---|---|---|
| Framework | React 19 + Vite | FastAPI + Jinja2 |
| Routing client-side | React Router DOM v7 | FastAPI Router (server-side) |
| Estado global | Zustand + localStorage | Sesiones FastAPI (signed cookies) |
| HTTP client | Axios | httpx (async) |
| Formularios | React controlled forms | HTMX + HTML forms |
| Renderizado dinámico | React re-renders | HTMX swap (hx-get, hx-post) |
| Paginación | React state + API call | HTMX + query params |
| Modales | React state + JSX | HTMX modals (hx-target) |
| Toast notifications | react-hot-toast | HTMX hx-trigger + JS toast |
| Mapas | react-leaflet | Leaflet vía CDN + JS inline |
| Gráficas | Recharts | Chart.js vía CDN |
| Estilos | Tailwind CSS v4 (Vite plugin) | Tailwind CSS v4 (CDN play) |
| Build tool | Vite | No necesario (server-side) |

## Estructura de Archivos: React → Python

```
REACT (original)                          PYTHON (nuevo)
─────────────────────────────────         ─────────────────────────────────
src/main.jsx                              app/main.py
src/app/App.jsx                           app/main.py (routes)
src/app/router/AppRoutes.jsx              app/routers/*.py
src/app/router/ProtectedRoute.py          app/middlewares/auth.py
src/shared/api/api.js                     app/api_client.py
src/shared/api/auth.js                    app/routers/auth.py
src/shared/api/admin.js                   app/api_client.py
src/shared/components/Pagination.jsx      HTMX hx-get + query params
src/shared/components/layout/             app/templates/base.html
  DashboardContainer.jsx                    (navbar + sidebar + content)
  Navbar.jsx                                (en base.html)
  Sidebar.jsx                               (en base.html)
src/features/auth/authStore.js            Sesiones FastAPI
src/features/auth/pages/AuthPage.jsx      app/templates/auth/login.html
src/features/auth/components/             app/templates/auth/
  LoginForm.jsx                             login.html
  ForgotPasswordForm.jsx                    login.html (sección)
src/features/dashboard/components/        app/templates/dashboard/
  DashboardOverview.jsx                     index.html
src/features/roads/roadsStore.js          app/routers/roads.py
src/features/roads/components/            app/templates/roads/
  Roads.jsx                                 index.html
  RoadModal.jsx                             index.html (modal HTMX)
src/features/stations/                    app/routers/stations.py + templates/
src/features/buses/                       app/routers/buses.py + templates/
src/features/alerts/                      app/routers/alerts.py + templates/
src/features/users/                       app/routers/users.py + templates/
```

## Mapeo de Componentes React → Jinja2+HTMX

### Layout
- `DashboardContainer.jsx` → `base.html` con `{% block content %}`
- `Navbar.jsx` → `<nav>` en `base.html`
- `Sidebar.jsx` → `<aside>` en `base.html` con HTMX navigation

### Auth
- `authStore.js` (login, logout, checkAuth) → `app/routers/auth.py` con `request.session`
- `LoginForm.jsx` → `auth/login.html` con `<form hx-post="/auth/login">`
- `ProtectedRoute.jsx` → Middleware en `app/routers/auth.py` con `Depends(require_auth)`

### Roads CRUD
- `roadsStore.js` (getRoads, createRoad, updateRoad, changeStatus) → `app/routers/roads.py`
- `Roads.jsx` (table + filters + pagination) → `roads/index.html` con HTMX pagination
- `RoadModal.jsx` (create/edit with Leaflet map) → `roads/index.html` modal section

### Stations CRUD
- Similar a Roads
- `StationModal.jsx` con Nominatim geocoding → JavaScript inline en template

### Buses CRUD
- `BusModal.jsx` con road dropdown → template con `<select>` HTMX

### Alerts
- `Alerts.jsx` (card grid) → `alerts/index.html` con HTMX
- `AlertModal.jsx` → modal en template

### Users
- `Users.jsx` (admin table) → `users/index.html`
- `AdminModal.jsx` → modal en template

### Dashboard
- `DashboardOverview.jsx` (stats + charts) → `dashboard/index.html` con Chart.js CDN

## API Client (httpx)

```python
# Equivalente a api.js + admin.js + auth.js
import httpx

ADMIN_URL = "http://localhost:3001/TCONECTA/v1"
AUTH_URL = "http://localhost:8080/api"

async def admin_request(method, path, token, **kwargs):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await client.request(method, f"{ADMIN_URL}{path}", headers=headers, **kwargs)
        return resp.json()

async def auth_request(method, path, **kwargs):
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, f"{AUTH_URL}{path}", **kwargs)
        return resp.json()
```

## Sesiones (equivalente a Zustand persist)

```python
# FastAPI sessions en cookies firmadas
from starlette.requests import Request

# Login: guardar token en sesión
request.session["token"] = data["token"]
request.session["user"] = decoded_user

# Logout: limpiar sesión
request.session.clear()

# Middleware: verificar auth
token = request.session.get("token")
if not token:
    return RedirectResponse("/auth/login")
```

## HTMX Patterns

### Paginación (reemplaza Pagination.jsx)
```html
<div hx-get="/roads?page=2" hx-target="#table-body" hx-swap="innerHTML">
  Siguiente
</div>
```

### Modal create/edit (reemplaza RoadModal.jsx)
```html
<button hx-get="/roads/new" hx-target="#modal">Crear</button>
<div id="modal"></div>
```

### Form submit (reemplaza store.createRoad)
```html
<form hx-post="/roads" hx-target="#roads-table" hx-swap="outerHTML">
  <input name="name" />
  <button type="submit">Guardar</button>
</form>
```

## Mapas Leaflet (sin react-leaflet)

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const map = L.map('map').setView([14.62, -90.52], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
</script>
```

## Variables de entorno

```
SECRET_KEY=super-secret-key-for-sessions
AUTH_URL=http://localhost:8080/api
ADMIN_URL=http://localhost:3001/TCONECTA/v1
```
