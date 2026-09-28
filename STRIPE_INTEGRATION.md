# Integración Stripe - T-Conecta
=================================

Guía completa para integrar Stripe PaymentIntents en modo TEST (sandbox).

---

## 📁 Estructura de Archivos

```
backend/Auth-Python/
├── .env.stripe.example          # Template variables entorno (NO commitear .env real)
├── app/
│   ├── services/
│   │   └── stripe_service.py    # Servicio core Stripe (PaymentIntents, refunds, webhooks)
│   ├── routers/
│   │   └── stripe.py            # Endpoints API (/api/stripe/*)
│   └── config.py                # Agregar STRIPE_SECRET_KEY, STRIPE_API_VERSION

frontend/Client-UserPY/
├── .env.stripe.example          # Template variables entorno
├── app/
│   ├── templates/
│   │   └── wallet/
│   │       └── stripe_elements.html  # Partial Stripe.js Elements
│   ├── config.py                # Agregar STRIPE_PUBLISHABLE_KEY
│   └── routers/
│       └── wallet.py            # Modificar para usar Stripe

STRIPE_INTEGRATION.md            # Este archivo
```

---

## 🔐 Variables de Entorno (NO COMMITEAR)

### Backend (Auth-Python)
```bash
# backend/Auth-Python/.env
STRIPE_SECRET_KEY=sk_test_TU_SECRET_KEY_AQUI
STRIPE_API_VERSION=2024-06-20
STRIPE_WEBHOOK_SECRET=whsec_TU_WEBHOOK_SECRET_AQUI  # Opcional, para webhooks
```

### Frontend (Client-UserPY)
```bash
# frontend/Client-UserPY/.env
STRIPE_PUBLISHABLE_KEY=pk_test_TU_PUBLISHABLE_KEY_AQUI
```

### En Render Dashboard
| Servicio | Variables |
|----------|-----------|
| `tconecta-auth` | `STRIPE_SECRET_KEY`, `STRIPE_API_VERSION`, `STRIPE_WEBHOOK_SECRET` |
| `tconecta-client-user` | `STRIPE_PUBLISHABLE_KEY` |

---

## 🚀 Flujo de Integración

### 1. Backend: Registrar Router Stripe

En `backend/Auth-Python/app/main.py`:
```python
from app.routers import auth, transaction, wallet, stripe  # Agregar stripe

app.include_router(stripe.router, prefix="/api/stripe", tags=["Stripe"])
```

### 2. Backend: Config Settings

En `backend/Auth-Python/app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing ...
    STRIPE_SECRET_KEY: str = ""
    STRIPE_API_VERSION: str = "2024-06-20"
    STRIPE_WEBHOOK_SECRET: str = ""
```

### 3. Frontend: Config Settings

En `frontend/Client-UserPY/app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing ...
    STRIPE_PUBLISHABLE_KEY: str = ""
```

### 3. Frontend: Pasar Key a Templates

En `frontend/Client-UserPY/app/main.py`:
```python
from app.config import settings

templates = Jinja2Templates(
    directory="app/templates",
    env=Environment(globals={"STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY})
)
```

### 4. Frontend: Incluir Partial en Wallet

En `frontend/Client-UserPY/app/templates/wallet/index.html`:
```html
<!-- Reemplazar formulario tarjeta actual (líneas ~96-108) por: -->
<div id="stripe-card-form">
    {% include "wallet/stripe_elements.html" %}
</div>

<!-- Ocultar inputs originales -->
<div class="original-card-inputs hidden">
    <!-- inputs cardNumber, expirationDate, cvv originales -->
</div>
```

---

## 💳 Flujo de Pago Completo

```
┌─────────────┐     1. POST /api/stripe/create-payment-intent
│  Usuario    │──────────────────────────────────────►
│  (Frontend) │     {amount: 1000, currency: "gtq"}
└─────────────┘
       │
       ▼
┌─────────────┐     2. Retorna {client_secret, payment_intent_id}
│  Auth API   │◄──────────────────────────────────────
│  (Backend)  │
└─────────────┘
       │
       ▼
┌─────────────┐     3. Stripe.js confirmCardPayment(client_secret)
│  Stripe.js  │──────────────────────────────────────►
│  (Frontend) │     Tarjeta tokenizada, 3D Secure si aplica
└─────────────┘
       │
       ▼
┌─────────────┐     4. POST /wallet/recharge {payment_intent_id}
│  Frontend   │──────────────────────────────────────►
│  Server     │
└─────────────┘
       │
       ▼
┌─────────────┐     5. Verifica payment_intent.succeeded
│  Auth API   │──────────────────────────────────────►
│  (Backend)  │     create_invoice() → redirect /wallet/{id}
└─────────────┘
       │
       ▼
┌─────────────┐
│  Usuario    │     Ve factura detalle
│  ve factura │
└─────────────┘
```

---

## 🧪 Tarjetas de Prueba (NO cobran)

| Escenario | Número | Exp | CVC |
|-----------|--------|-----|-----|
| ✅ Éxito | `4242 4242 4242 4242` | 12/30 | 123 |
| ❌ Rechazada | `4000 0000 0000 0002` | 12/30 | 123 |
| 🔐 3D Secure | `4000 0025 0000 3155` | 12/30 | 123 |
| ✅ Mastercard | `5555 5555 5555 4444` | 12/30 | 123 |
| ✅ Amex | `3782 8224 6310 005` | 12/30 | 1234 |

**Todas en modo TEST con claves `sk_test_` / `pk_test_`**

---

## 🔧 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/stripe/create-payment-intent` | Crea PaymentIntent, retorna `client_secret` |
| `POST` | `/api/stripe/confirm-payment` | Confirma PaymentIntent manualmente |
| `GET` | `/api/stripe/payment-intent/{id}` | Obtiene estado de pago |
| `POST` | `/api/stripe/refund` | Crea reembolso (Admin) |
| `POST` | `/api/stripe/webhook` | Webhook Stripe (async events) |
| `GET` | `/api/stripe/test-cards` | Tarjetas de prueba oficiales |

---

## 📝 Modificaciones en Wallet Router

En `frontend/Client-UserPY/app/routers/wallet.py`:

```python
# Agregar import
from app.config import STRIPE_PUBLISHABLE_KEY

# Modificar recarga para aceptar payment_intent_id
@router.post("/recharge")
async def recharge(
    request: Request,
    amount: float = Form(...),
    cardNumber: str = Form(...),  # "stripe_payment" si viene de Stripe
    expirationDate: str = Form(...),
    cvv: str = Form(...),
    payment_intent_id: str = Form(None),  # Nuevo
):
    # Si payment_intent_id presente → verificar con Stripe
    if payment_intent_id:
        # Verificar payment_intent.succeeded via Stripe API
        # Si OK → create_invoice() → redirect
    
    # Flujo original (fallback)
    ...
```

---

## 🔄 Webhooks (Opcional - Para Producción)

### Configurar en Stripe Dashboard
```
URL: https://tconecta-auth.onrender.com/api/stripe/webhook
Eventos:
  - payment_intent.succeeded
  - payment_intent.payment_failed
  - charge.refunded
  - payment_method.attached
```

### En .env backend
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxx
```

### Evento payment_intent.succeeded
```python
# En stripe.py webhook handler
if event_type == "payment_intent.succeeded":
    payment_intent = event["data"]["object"]
    user_id = payment_intent["metadata"]["user_id"]
    # create_invoice_from_payment(user_id, payment_intent)
```

---

## ✅ Checklist de Implementación

### Backend
- [ ] Copiar `.env.stripe.example` → `.env` con keys reales
- [ ] Agregar `stripe_service.py` y `stripe.py` router
- [ ] Registrar router en `main.py`
- [ ] Agregar settings en `config.py`
- [ ] Instalar `stripe` en `pyproject.toml` / `requirements.txt`

### Frontend
- [ ] Copiar `.env.stripe.example` → `.env` con publishable key
- [ ] Agregar `STRIPE_PUBLISHABLE_KEY` a `config.py`
- [ ] Pasar key a templates en `main.py`
- [ ] Incluir `stripe_elements.html` en `wallet/index.html`
- [ ] Modificar `wallet.py` para manejar `payment_intent_id`

### Deploy (Render)
- [ ] Agregar variables en Dashboard cada servicio
- [ ] Configurar webhook URL en Stripe Dashboard
- [ ] Probar en staging con tarjetas de prueba

---

## 🚫 Qué NO Hacer

| ❌ No hacer | ✅ Hacer en su lugar |
|-------------|---------------------|
| Hardcodear keys en código | Usar variables de entorno |
| Commitear `.env` real | Usar `.env.example` + documentar |
| Usar claves LIVE en dev | Solo `sk_test_` / `pk_test_` |
| Guardar datos tarjeta en BD | Stripe tokeniza todo (PCI SAQ A) |
| Probar con tarjetas reales | Usar tarjetas de prueba oficiales |

---

## 📚 Referencias

- [Stripe PaymentIntents Docs](https://stripe.com/docs/payments/payment-intents)
- [Stripe.js Elements](https://stripe.com/docs/stripe-js)
- [Stripe Testing](https://stripe.com/docs/testing)
- [PCI SAQ A](https://stripe.com/docs/security#validating-pci-compliance)

---

## 📝 Notas para el Equipo

1. **Archivos creados (local only, no push):**
   - `backend/Auth-Python/.env.stripe.example`
   - `backend/Auth-Python/app/services/stripe_service.py`
   - `backend/Auth-Python/app/routers/stripe.py`
   - `frontend/Client-UserPY/.env.stripe.example`
   - `frontend/Client-UserPY/app/templates/wallet/stripe_elements.html`
   - `STRIPE_INTEGRATION.md` (este archivo)

2. **Para activar:** Copiar `.env.stripe.example` → `.env` con keys reales, instalar dependencias, registrar routers.

3. **Testing:** Usar tarjetas de prueba oficiales. El mock test actual sigue funcionando para CI rápido.

4. **Producción:** Cambiar a claves `sk_live_` / `pk_live_`, configurar webhooks reales, revisar compliance PCI.