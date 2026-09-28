# ESPECIFICACIÓN: Agregar Facturas / Invoices

---

## Contexto del Proyecto

- **Monorepo**: 6 microservicios Python independientes (sin workspace compartido)
- **Auth-Python** (puerto 5001/8080): Genera JWT, maneja transacciones (recarga/compra tarjeta) → **MongoDB `TransmetroUserDb` colecciones `wallets`**
- **Client-UserPY** (puerto 5174): SSR FastAPI+Jinja2, proxy a Auth-Server → **Wallet view con tabs: Recarga / Compra / Historial**
- **Flujo actual transacción**: Luhn → `asyncio.sleep(1.5)` → MongoDB update → redirect a `/wallet?tab=...` con toast

---

## Objetivo

Agregar funcionalidad de **facturas** que se genere automáticamente tras cada transacción exitosa (recarga o compra tarjeta), con:
1. **Vista detalle** en wallet: `/wallet/[mongo_id_factura]` (URL persiste)
2. **Listado paginado** en nueva tab "Facturas" en wallet
3. **Datos factura**: fecha, monto, nombre usuario (CUI), últimos 4 tarjeta, tipo (recarga/compra)
4. **Responsive** (Tailwind CDN), mismo patrón visual que wallet actual
5. **Sin migraciones** — MongoDB schemaless, solo nueva colección o extendido

---

## 1. Análisis de Impacto en Base de Datos (MongoDB)

### Colección actual `wallets`:
```json
{
  "_id": "user_uuid",
  "saldo": 125.00,
  "viajesCortesia": 5,
  "hasCitizenCard": true,
  "historialRecargas": [{ "monto": 25.00, "fecha": "2026-09-14T05:00:00Z" }],
  "created_at": "...", "updated_at": "..."
}
```

### Opción A — Nueva colección `invoices` (RECOMENDADA)
- No toca `wallets` existente (cero riesgo en producción)
- Índice por `userId` + `createdAt` para paginación eficiente
- Documento factura:
```json
{
  "_id": "ObjectId",
  "userId": "user_uuid",
  "tipo": "RECARGA" | "COMPRA_TARJETA",
  "monto": 25.00,
  "fecha": "2026-09-14T05:00:00Z",
  "tarjetaUltimos4": "0366",
  "cuiUsuario": "2000000000002",
  "transactionId": "uuid-de-transaccion",
  "status": "COMPLETADA"
}
```

### Opción B — Extender `wallets` con array `facturas`
- Más simple, pero crece documento indefinidamente
- Requiere `$push` atómico (ya se usa para `historialRecargas`)

**Decisión**: **Opción A** — Nueva colección `invoices` en `TransmetroUserDb`. Cero migración, escalable, índices propios.

---

## 2. Backend — Auth-Python

### Archivos a crear/modificar:

#### `app/services/invoice_service.py` (NUEVO)
```python
from datetime import datetime, timezone
from app.database_mongo import get_mongo_db
import uuid

async def create_invoice(
    user_id: str,
    cui: str,
    tipo: str,           # "RECARGA" | "COMPRA_TARJETA"
    monto: float,
    tarjeta_ultimos4: str,
    transaction_id: str
) -> str | None:
    """
    Crea factura en MongoDB y retorna el ObjectId como string.
    """
    try:
        mongo_db = get_mongo_db()
        now = datetime.now(timezone.utc)
        
        invoice_doc = {
            "userId": user_id,
            "cuiUsuario": cui,
            "tipo": tipo,
            "monto": round(monto, 2),
            "fecha": now,
            "tarjetaUltimos4": tarjeta_ultimos4,
            "transactionId": transaction_id,
            "status": "COMPLETADA",
            "created_at": now,
        }
        result = await mongo_db.invoices.insert_one(invoice_doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[InvoiceService] Error creando factura: {e}")
        return None


async def get_user_invoices(user_id: str, page: int = 1, limit: int = 10) -> dict:
    """
    Retorna facturas paginadas del usuario.
    """
    try:
        mongo_db = get_mongo_db()
        skip = (page - 1) * limit
        
        cursor = mongo_db.invoices.find({"userId": user_id}).sort("fecha", -1).skip(skip).limit(limit)
        invoices = await cursor.to_list(length=limit)
        
        total = await mongo_db.invoices.count_documents({"userId": user_id})
        total_pages = max(1, (total + limit - 1) // limit)
        
        # Convertir ObjectId a string para JSON
        for inv in invoices:
            inv["_id"] = str(inv["_id"])
            inv["fecha"] = inv["fecha"].isoformat() if hasattr(inv["fecha"], "isoformat") else str(inv["fecha"])
        
        return {
            "invoices": invoices,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages
        }
    except Exception as e:
        print(f"[InvoiceService] Error obteniendo facturas: {e}")
        return {"invoices": [], "total": 0, "page": 1, "limit": limit, "totalPages": 1}


async def get_invoice_by_id(invoice_id: str, user_id: str) -> dict | None:
    """
    Obtiene factura por ID verificando ownership.
    """
    try:
        from bson import ObjectId
        mongo_db = get_mongo_db()
        invoice = await mongo_db.invoices.find_one({
            "_id": ObjectId(invoice_id),
            "userId": user_id
        })
        if invoice:
            invoice["_id"] = str(invoice["_id"])
            invoice["fecha"] = invoice["fecha"].isoformat() if hasattr(invoice["fecha"], "isoformat") else str(invoice["fecha"])
        return invoice
    except Exception as e:
        print(f"[InvoiceService] Error obteniendo factura: {e}")
        return None
```

#### Modificar `app/services/transaction_service.py`
- Importar `create_invoice` al inicio
- En `process_payment()` y `purchase_card()`: tras éxito, llamar `create_invoice()` con datos de la transacción
- El `transactionId` que ya se genera (uuid) se pasa a la factura

```python
# En process_payment() - tras wallet_updated exitoso:
from app.services.invoice_service import create_invoice
# Obtener CUI del usuario (desde user_id en PostgreSQL o pasarlo desde router)
invoice_id = await create_invoice(
    user_id=user_id,
    cui=usuario_cui,  # necesitas pasarlo desde el router
    tipo="RECARGA",
    monto=amount,
    tarjeta_ultimos4=card_number[-4:],
    transaction_id=transaction_id
)
# Retornar invoice_id en response para redirect

# En purchase_card() - similar:
invoice_id = await create_invoice(
    user_id=user_id,
    cui=usuario_cui,
    tipo="COMPRA_TARJETA",
    monto=20.00,
    tarjeta_ultimos4=card_number[-4:],
    transaction_id=transaction_id
)
```

#### Modificar `app/routers/transaction.py`
- Obtener CUI del usuario autenticado (desde `user` model)
- Pasar CUI a `transaction_service`
- Retornar `invoiceId` en response:
```python
return {
    "isSuccess": True,
    "message": "...",
    "transactionId": str(uuid.uuid4()),
    "invoiceId": invoice_id  # NUEVO
}
```

#### Modificar `app/schemas/auth.py`
- Agregar `invoiceId: str | None = None` a `TransactionResponse`

---

## 3. Frontend — Client-UserPY

### Archivos a crear/modificar:

#### `app/routers/wallet.py` — Agregar rutas

```python
# NUEVO: Vista detalle factura
@router.get("/{invoice_id}")
async def invoice_detail(request: Request, invoice_id: str):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        # Llamar a Auth-Server para obtener factura
        invoice = await auth_request("GET", f"/wallets/invoice/{invoice_id}", token=token)
        if not invoice:
            raise HTTPException(404, "Factura no encontrada")
    except Exception:
        raise HTTPException(404, "Factura no encontrada")
    
    # Parsear fecha para template
    from datetime import datetime
    fecha = datetime.fromisoformat(invoice["fecha"].replace("Z", "+00:00"))
    
    return templates.TemplateResponse(request, "wallet/invoice_detail.html", {
        "user": user,
        "invoice": invoice,
        "fecha_formateada": fecha.strftime("%d/%m/%Y %H:%M"),
    })


# NUEVO: API para listar facturas (usada por tab Facturas)
@router.get("/api/invoices")
async def get_invoices_api(request: Request, page: int = Query(1)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(401, "Unauthorized")
    token = request.session.get("token")
    try:
        data = await auth_request("GET", f"/wallets/invoices?page={page}&limit=10", token=token)
        return data
    except Exception:
        return {"invoices": [], "total": 0, "page": 1, "limit": 10, "totalPages": 1}
```

#### `app/api_client.py` — Agregar métodos
```python
# En la clase AuthClient o funciones auth_request
async def get_invoice(invoice_id: str, token: str) -> dict:
    return await _request("GET", f"/wallets/invoice/{invoice_id}", token=token)

async def get_invoices(page: int = 1, limit: int = 10, token: str = None) -> dict:
    return await _request("GET", f"/wallets/invoices?page={page}&limit={limit}", token=token)
```

#### `app/templates/wallet/index.html` — Agregar tab "Facturas"
```html
<!-- En tabs header (línea ~69-79), agregar 4ta tab: -->
<a href="/wallet?tab=invoices" class="flex-1 py-4 font-bold text-sm transition-colors text-center flex items-center justify-center gap-1 {% if tab == 'invoices' %}border-b-2 border-[#46bf00] text-[#1801a9] bg-[#46bf00]/10{% else %}text-gray-500 hover:text-[#1801a9]{% endif %}">
    Facturas
</a>

<!-- En tab body (línea ~82-174), agregar bloque elif tab == "invoices": -->
{% elif tab == "invoices %}
<div class="space-y-4">
    <h2 class="text-lg font-bold text-[#1801a9] mb-4">Facturas Emitidas</h2>
    {% if not invoices %}
    <div class="text-center py-10 text-gray-400">
        <p class="text-sm font-medium">No hay facturas emitidas</p>
        <p class="text-xs mt-1">Tus facturas aparecerán aquí tras cada recarga o compra</p>
    </div>
    {% else %}
    <div class="space-y-2 max-w-lg mx-auto">
        {% for inv in invoices %}
        <a href="/wallet/{{ inv._id }}" class="block p-4 bg-gray-50 rounded-xl border border-gray-100 hover:bg-gray-100 transition-colors">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 {% if inv.tipo == 'RECARGA' %}bg-[#46bf00]/10 text-[#46bf00]{% else %}bg-[#1801a9]/10 text-[#1801a9]{% endif %} rounded-full flex items-center justify-center font-bold text-sm">
                        {% if inv.tipo == 'RECARGA' %}Q{% else %}🎫{% endif %}
                    </div>
                    <div>
                        <p class="font-bold text-sm text-gray-900">
                            {% if inv.tipo == 'RECARGA' %}Recarga de Saldo{% else %}Compra Tarjeta Ciudadana{% endif %}
                        </p>
                        <p class="text-xs text-gray-500">{{ inv.fecha[:10] }} • Tarjeta •••• {{ inv.tarjetaUltimos4 }}</p>
                    </div>
                </div>
                <span class="px-2 py-0.5 text-xs font-semibold text-emerald-800 bg-emerald-100 rounded-full">
                    Q{{ "%.2f"|format(inv.monto) }}
                </span>
            </div>
        </a>
        {% endfor %}
    </div>
    <!-- Paginación igual que historial -->
    <div class="flex justify-center gap-2 mt-6">
        {% if page > 1 %}<a href="/wallet?tab=invoices&page={{ page-1 }}" class="px-4 py-2 rounded-lg border text-sm font-bold text-gray-600 hover:bg-gray-50">Anterior</a>{% endif %}
        <span class="px-4 py-2 text-sm font-bold text-[#1801a9] bg-gray-50 rounded-lg">Página {{ page }} de {{ total_pages }}</span>
        {% if page < total_pages %}<a href="/wallet?tab=invoices&page={{ page+1 }}" class="px-4 py-2 rounded-lg border text-sm font-bold text-gray-600 hover:bg-gray-50">Siguiente</a>{% endif %}
    </div>
    {% endif %}
</div>
{% endif %}
```

#### `app/templates/wallet/invoice_detail.html` (NUEVO)
```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-2xl mx-auto space-y-6 py-8 px-4">
    <!-- Header con botón volver -->
    <div class="flex items-center gap-4">
        <a href="/wallet?tab=invoices" class="p-2 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </a>
        <div>
            <h1 class="text-2xl font-black text-[#1801a9]">Factura</h1>
            <p class="text-sm text-gray-500">{{ fecha_formateada }}</p>
        </div>
    </div>

    <!-- Card Factura -->
    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
        <div class="bg-gradient-to-r from-[#1801a9] to-indigo-900 text-white p-6">
            <div class="flex justify-between items-start">
                <div>
                    <span class="text-xs font-bold uppercase tracking-widest text-[#46bf00]">
                        {% if invoice.tipo == "RECARGA" %}RECARGA DE SALDO{% else %}COMPRA TARJETA CIUDADANA{% endif %}
                    </span>
                    <p class="text-sm text-blue-100 mt-1">T-Conecta • Transmetro Conecta</p>
                </div>
                <div class="text-right">
                    <p class="text-3xl font-black">Q{{ "%.2f"|format(invoice.monto) }}</p>
                    <p class="text-xs text-blue-200">Monto Total</p>
                </div>
            </div>
        </div>

        <div class="p-6 space-y-5">
            <!-- Info Transacción -->
            <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                <h3 class="text-xs font-bold text-[#1801a9] uppercase tracking-wider mb-3">Detalle de Transacción</h3>
                <dl class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <dt class="text-gray-500">ID Factura</dt>
                        <dd class="font-mono font-bold text-gray-900">{{ invoice._id }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">ID Transacción</dt>
                        <dd class="font-mono font-bold text-gray-900">{{ invoice.transactionId }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Fecha y Hora</dt>
                        <dd class="font-bold text-gray-900">{{ fecha_formateada }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Estado</dt>
                        <dd class="px-2 py-0.5 text-xs font-semibold text-emerald-800 bg-emerald-100 rounded-full">{{ invoice.status }}</dd>
                    </div>
                </dl>
            </div>

            <!-- Info Usuario -->
            <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                <h3 class="text-xs font-bold text-[#1801a9] uppercase tracking-wider mb-3">Datos del Usuario</h3>
                <dl class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <dt class="text-gray-500">CUI / DPI</dt>
                        <dd class="font-mono font-bold text-gray-900">{{ invoice.cuiUsuario }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Tarjeta</dt>
                        <dd class="font-mono font-bold text-gray-900">•••• {{ invoice.tarjetaUltimos4 }}</dd>
                    </div>
                </dl>
            </div>

            <!-- Código QR placeholder -->
            <div class="text-center py-4">
                <div class="w-32 h-32 mx-auto bg-gray-100 rounded-xl flex items-center justify-center border border-gray-200">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                </div>
                <p class="text-xs text-gray-500 mt-2">Código de verificación</p>
            </div>

            <!-- Acciones -->
            <div class="flex gap-3 pt-4 border-t border-gray-100">
                <button onclick="window.print()" class="flex-1 bg-[#1801a9] hover:opacity-90 text-white font-bold py-3 rounded-xl transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
                    Imprimir / Guardar PDF
                </button>
                <a href="/wallet?tab=invoices" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 rounded-xl transition-all text-center">
                    Volver al Listado
                </a>
            </div>
        </div>
    </div>

    <!-- Footer legal -->
    <div class="text-center text-xs text-gray-400">
        <p>Esta factura es un comprobante digital emitido por T-Conecta.</p>
        <p>Municipalidad de Guatemala • Sistema Transmetro Conecta</p>
    </div>
</div>
{% endblock %}
```

#### Modificar `app/routers/wallet.py` — wallet_page()
- Agregar lógica para `tab == "invoices"`: llamar `get_invoices_api` o `client_request` a `/wallets/invoices`
- Pasar `invoices`, `page`, `total_pages` al template

---

## 4. Auth-Python — Nuevos Endpoints (en `app/routers/wallet.py` o nuevo router)

```python
# En backend/Auth-Python/app/routers/wallet.py (existente o nuevo)

from app.services.invoice_service import get_user_invoices, get_invoice_by_id
from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User

@router.get("/invoices")
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(validate_jwt),
):
    result = await get_user_invoices(user.id, page, limit)
    return result


@router.get("/invoice/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: User = Depends(validate_jwt),
):
    invoice = await get_invoice_by_id(invoice_id, user.id)
    if not invoice:
        raise HTTPException(404, "Factura no encontrada")
    return invoice
```

---

## 5. Flujo Completo (Usuario)

```
1. Usuario en /wallet → tab "Recargar Saldo"
2. Llena formulario → POST /wallet/recharge
3. Client-UserPY → Auth-Server POST /api/transaction/recharge
4. Auth-Server:
   a) Valida Luhn
   b) asyncio.sleep(1.5)  # Simula pasarela
   c) Actualiza wallet (saldo + historialRecargas)
   d) CREA factura en colección invoices
   e) Retorna { isSuccess, transactionId, invoiceId }
5. Client-UserPY recibe respuesta → Redirect a /wallet/[invoiceId]
6. GET /wallet/[invoiceId] → Render invoice_detail.html con datos
7. URL se queda en /wallet/[mongo_id] (persistente, compartible)
8. Usuario puede: ver detalle, imprimir/PDF, volver a listado
9. En tab "Facturas" → listado paginado con enlace a cada detalle
```

---

## 6. Checklist de Implementación

### Backend (Auth-Python)
- [ ] Crear `app/services/invoice_service.py`
- [ ] Modificar `app/services/transaction_service.py` → llamar `create_invoice` en ambos métodos
- [ ] Modificar `app/schemas/auth.py` → agregar `invoiceId` en `TransactionResponse`
- [ ] Modificar `app/routers/transaction.py` → pasar CUI y retornar `invoiceId`
- [ ] Crear/agregar en `app/routers/wallet.py` endpoints `GET /invoices` y `GET /invoice/{id}`
- [ ] Verificar índices MongoDB: `db.invoices.createIndex({ userId: 1, fecha: -1 })`

### Frontend (Client-UserPY)
- [ ] Agregar métodos en `app/api_client.py` para facturas
- [ ] Agregar rutas en `app/routers/wallet.py`: `GET /{invoice_id}`, `GET /api/invoices`
- [ ] Modificar `app/templates/wallet/index.html` → tab "Facturas" + bloque contenido
- [ ] Crear `app/templates/wallet/invoice_detail.html`
- [ ] Ajustar `wallet_page()` para manejar `tab=invoices`

### Testing
- [ ] Test E2E: recarga → verificar redirect a `/wallet/[id]` → ver factura
- [ ] Test E2E: compra tarjeta → verificar factura tipo COMPRA_TARJETA
- [ ] Test E2E: tab Facturas → paginación → click factura → detalle
- [ ] Verificar responsive en móvil (Tailwind)
- [ ] Verificar ownership: usuario A no ve facturas de usuario B

---

## 10. Tests Playwright (basados en tests existentes)

### Patrones de referencia del proyecto
- **Fixture**: `login_user` en `test/conftest.py` (retry automático 3×5s por rate limiting 429)
- **URL base**: `USER_URL = "http://localhost:5174"`
- **Selectores**: `get_by_role`, `get_by_text`, `locator("input[name='...']")`, `get_by_role("button", name=re.compile(...))`
- **Navegación**: `expect(page).to_have_url(re.compile(...), timeout=10000)`
- **Tabs**: botones con `name="..."` en header, `href="/wallet?tab=..."`

### Archivo: `test/test_user_invoices.py` (NUEVO)

```python
import re
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

# Tarjeta válida Luhn para tests (Visa test)
VALID_CARD = "4532015112830366"
VALID_EXP = "12/28"
VALID_CVV = "123"

# ──────────────────────────────────────────────
# FACTURA TRAS RECARGA
# ──────────────────────────────────────────────
def test_invoice_created_after_recharge(login_user: Page):
    """
    1. Ir a wallet → tab recarga
    2. Hacer recarga Q10 con tarjeta válida
    3. Verificar redirect a /wallet/[ObjectId] (factura detalle)
    4. Verificar datos clave en factura: monto, tipo, CUI, últimos 4 tarjeta
    """
    login_user.goto(f"{USER_URL}/wallet")
    
    # Esperar formulario recarga (tab por defecto)
    login_user.get_by_role("button", name="Q10.00").wait_for(state="visible")
    
    # Llenar y enviar
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    
    # Click y esperar navegación a factura
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # Verificar URL: /wallet/[mongo_id] (ObjectId de 24 hex chars)
    expect(login_user).to_have_url(re.compile(r"/wallet/[a-f0-9]{24}$"), timeout=10000)
    
    # Verificar contenido factura detalle
    expect(login_user.get_by_role("heading", name="Factura")).to_be_visible()
    expect(login_user.get_by_text("RECARGA DE SALDO")).to_be_visible()
    expect(login_user.get_by_text("Q10.00")).to_be_visible()
    expect(login_user.get_by_text("COMPLETADA")).to_be_visible()
    # CUI del usuario de test (2000000000002)
    expect(login_user.get_by_text("2000000000002")).to_be_visible()
    # Últimos 4 de tarjeta de test
    expect(login_user.get_by_text("0366")).to_be_visible()
    
    # Verificar botones de acción
    expect(login_user.get_by_role("button", name=re.compile(r"Imprimir"))).to_be_visible()
    expect(login_user.get_by_role("link", name="Volver al Listado")).to_be_visible()


# ──────────────────────────────────────────────
# FACTURA TRAS COMPRA TARJETA
# ──────────────────────────────────────────────
def test_invoice_created_after_purchase_card(login_user: Page):
    """
    1. Ir a wallet → tab compra tarjeta
    2. Comprar tarjeta Q20.00
    3. Verificar redirect a factura con tipo COMPRA_TARJETA
    """
    login_user.goto(f"{USER_URL}/wallet?tab=purchase")
    
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).wait_for(state="visible")
    
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    
    with login_user.expect_navigation():
        login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).click()
    
    # Verificar URL factura
    expect(login_user).to_have_url(re.compile(r"/wallet/[a-f0-9]{24}$"), timeout=10000)
    
    # Verificar tipo COMPRA_TARJETA
    expect(login_user.get_by_text("COMPRA TARJETA CIUDADANA")).to_be_visible()
    expect(login_user.get_by_text("Q20.00")).to_be_visible()
    expect(login_user.get_by_text("2000000000002")).to_be_visible()
    expect(login_user.get_by_text("0366")).to_be_visible()


# ──────────────────────────────────────────────
# TAB FACTURAS — LISTADO PAGINADO
# ──────────────────────────────────────────────
def test_invoices_tab_list_pagination(login_user: Page):
    """
    1. Ir a tab Facturas
    2. Verificar listado (vacío o con facturas previas)
    3. Verificar paginación si hay >10 facturas
    """
    login_user.goto(f"{USER_URL}/wallet?tab=invoices")
    
    # Tab Facturas activa
    expect(login_user.get_by_role("heading", name="Facturas Emitidas")).to_be_visible()
    
    # Si no hay facturas → mensaje vacío
    empty_state = login_user.get_by_text("No hay facturas emitidas")
    if empty_state.count() > 0:
        expect(empty_state).to_be_visible()
        expect(login_user.get_by_text("Tus facturas aparecerán aquí")).to_be_visible()
        return
    
    # Si hay facturas → verificar estructura listado
    # Cada factura es un enlace <a href="/wallet/[id]">
    first_invoice_link = login_user.locator("a[href^='/wallet/']").first
    expect(first_invoice_link).to_be_visible()
    
    # Verificar elementos de cada fila
    expect(first_invoice_link.locator("text=Q")).to_be_visible()  # monto
    expect(first_invoice_link.locator("text=COMPLETADA")).to_be_visible()  # estado
    
    # Paginación (si total_pages > 1)
    pagination = login_user.get_by_text(re.compile(r"Página \d+ de \d+"))
    if pagination.count() > 0:
        expect(pagination).to_be_visible()
        # Test navegar páginas
        next_btn = login_user.get_by_role("link", name="Siguiente")
        if next_btn.count() > 0:
            with login_user.expect_navigation():
                next_btn.click()
            expect(login_user).to_have_url(re.compile(r"tab=invoices&page=2"))


# ──────────────────────────────────────────────
# NAVEGACIÓN: LISTADO → DETALLE → VOLVER
# ──────────────────────────────────────────────
def test_invoice_list_to_detail_navigation(login_user: Page):
    """
    1. Crear factura vía recarga (reutiliza test anterior)
    2. Ir a tab Facturas
    3. Click en factura → ir a detalle
    4. Click "Volver al Listado" → regresa a tab Facturas
    """
    # 1. Crear factura (recarga rápida)
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # Capturar invoice_id de la URL
    invoice_url = login_user.url
    invoice_id_match = re.search(r"/wallet/([a-f0-9]{24})$", invoice_url)
    assert invoice_id_match, "URL debe terminar en /wallet/[ObjectId]"
    invoice_id = invoice_id_match.group(1)
    
    # 2. Ir a tab Facturas
    login_user.goto(f"{USER_URL}/wallet?tab=invoices")
    expect(login_user.get_by_role("heading", name="Facturas Emitidas")).to_be_visible()
    
    # 3. Click en la factura recién creada
    invoice_link = login_user.locator(f"a[href='/wallet/{invoice_id}']")
    expect(invoice_link).to_be_visible()
    
    with login_user.expect_navigation():
        invoice_link.click()
    
    # Verificar detalle
    expect(login_user).to_have_url(re.compile(rf"/wallet/{invoice_id}$"))
    expect(login_user.get_by_text("RECARGA DE SALDO")).to_be_visible()
    
    # 4. Volver al listado
    with login_user.expect_navigation():
        login_user.get_by_role("link", name="Volver al Listado").click()
    
    expect(login_user).to_have_url(re.compile(r"/wallet\?tab=invoices"))


# ──────────────────────────────────────────────
# OWNERSHIP — USUARIO A NO VE FACTURAS DE USUARIO B
# ──────────────────────────────────────────────
def test_invoice_ownership_isolation(login_user: Page, login_admin: Page):
    """
    1. Usuario crea factura → obtener invoice_id
    2. Admin intenta acceder a /wallet/[invoice_id]
    3. Debe fallar (404 o redirect) — ownership verificado en backend
    """
    # Usuario crea factura
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()
    
    invoice_url = login_user.url
    invoice_id_match = re.search(r"/wallet/([a-f0-9]{24})$", invoice_url)
    invoice_id = invoice_id_match.group(1)
    
    # Admin intenta acceder a factura del usuario
    login_admin.goto(f"{USER_URL}/wallet/{invoice_id}")
    
    # Backend debe retornar 404 (ownership check en get_invoice_by_id)
    # En SSR FastAPI, 404 renderiza página de error o redirige
    # Verificar que NO ve la factura del usuario
    expect(login_admin.get_by_text("RECARGA DE SALDO")).not_to_be_visible()
    # O verificar redirect a wallet sin factura
    expect(login_admin).to_have_url(re.compile(r"/wallet"))


# ──────────────────────────────────────────────
# RESPONSIVE — MÓVIL (375px)
# ──────────────────────────────────────────────
def test_invoice_detail_responsive_mobile(login_user: Page):
    """
    Verificar factura detalle en viewport móvil (375px)
    """
    # Crear factura primero
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # Redimensionar a móvil
    login_user.set_viewport_size({"width": 375, "height": 667})
    
    # Verificar que elementos clave siguen visibles y legibles
    expect(login_user.get_by_role("heading", name="Factura")).to_be_visible()
    expect(login_user.get_by_text("Q10.00")).to_be_visible()
    expect(login_user.get_by_text("COMPLETADA")).to_be_visible()
    
    # Botones apilados en móvil (flex-col en <640px)
    print_btn = login_user.get_by_role("button", name=re.compile(r"Imprimir"))
    back_link = login_user.get_by_role("link", name="Volver al Listado")
    expect(print_btn).to_be_visible()
    expect(back_link).to_be_visible()
    
    # No overflow horizontal
    body_width = login_user.evaluate("document.body.scrollWidth")
    assert body_width <= 375, f"Overflow horizontal detectado: {body_width}px"


# ──────────────────────────────────────────────
# COMANDOS DE EJECUCIÓN
# ──────────────────────────────────────────────
"""
# Instalar (si no está)
pip install playwright pytest pytest-html && playwright install chromium

# Correr tests de facturas
pytest test/test_user_invoices.py -v

# Con navegador visible
pytest test/test_user_invoices.py -v --headed

# Solo test específico
pytest test/test_user_invoices.py::test_invoice_created_after_recharge -v

# Con reporte HTML
pytest test/test_user_invoices.py -v --html=report.html

# Parar en primer fallo
pytest test/test_user_invoices.py -v -x
"""
```

### Notas de implementación tests

| Aspecto | Detalle |
|---------|---------|
| **Rate limiting** | `conftest.py` ya maneja retry 3×5s en `login_user` fixture |
| **Tarjeta Luhn** | `4532015112830366` es Visa test válida (pasa `is_valid_luhn`) |
| **Timeout** | 10000ms para navegación (incluye `asyncio.sleep(1.5)` backend) |
| **URL ObjectId** | Regex `[a-f0-9]{24}` valida MongoDB ObjectId hex |
| **Ownership** | Test usa dos fixtures: `login_user` + `login_admin` (distintos usuarios) |
| **Responsive** | `page.set_viewport_size({"width": 375, "height": 667})` para móvil |

---

## 7. Variables de Entorno / Config

**No se requieren nuevas variables** — usa MongoDB existente (`TransmetroUserDb`) y JWT_SECRET compartido.

---

## 8. Comandos de Verificación

```bash
# Backend
cd backend/Auth-Python && uv sync && uvicorn app.main:app --reload --port 5001

# Frontend
cd frontend/Client-UserPY && pip install -e . && uvicorn app.main:app --reload --port 5174

# MongoDB - verificar colección
mongosh "mongodb://localhost:27017/TransmetroUserDb" --eval "db.invoices.find().pretty()"

# Test manual
# 1. Login usuario
# 2. Ir a /wallet → Recargar Q10 con tarjeta válida Luhn (ej: 4111111111111111)
# 3. Verificar redirect a /wallet/[ObjectId]
# 4. Ver factura con datos correctos
# 5. Ir a tab Facturas → ver listado paginado
```

---

## 9. Notas de Diseño

- **Consistencia visual**: Usa mismos colores (`#1801a9`, `#46bf00`), sombras, bordes que `wallet/index.html`
- **Responsive**: Tailwind `max-w-2xl mx-auto`, `grid`, `flex` — probar en 375px, 768px, 1024px+
- **Sin HTMX real**: El proyecto carga HTMX pero usa full-page reloads → mantener ese patrón
- **Seguridad**: Endpoint factura verifica `userId` ownership en MongoDB query
- **Performance**: Índice compuesto `userId + fecha` para paginación O(log n)
- **Escalabilidad**: Colección separada evita documento `wallets` gigante