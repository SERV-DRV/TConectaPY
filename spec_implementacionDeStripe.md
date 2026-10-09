# Especificación de Implementación de Stripe — TConectaPY

## Resumen Ejecutivo

Este documento describe la implementación completa de Stripe como método de pago principal en producción, manteniendo el simulacro actual (basado en Luhn) para desarrollo. La arquitectura sigue **Clean Architecture** con archivos paralelos sufijos `-Stp`.

---

## 1. Arquitectura y Estructura de Archivos

### 1.1 Nuevos Archivos a Crear (sufijo `-Stp`)

```
backend/Auth-Python/app/
├── services/
│   ├── transaction_service-Stp.py      # Nueva implementación Stripe (paralela a transaction_service.py)
│   └── payment_gateway_factory.py      # Factory para switch entre Stripe/Simulación
├── schemas/
│   └── stripe_schemas.py               # Schemas específicos de Stripe
├── routers/
│   └── transaction.py                  # MODIFICAR: usar factory
└── config.py                           # MODIFICAR: agregar propiedades de entorno
```

### 1.2 Archivos Existentes a Modificar

| Archivo | Cambio |
|---------|--------|
| `config.py` | Agregar property `is_production` basada en `ENVIRONMENT` |
| `transaction_service.py` | Mantener como simulacro (development) |
| `transaction_service-Stp.py` | Nueva implementación Stripe (production) |
| `schemas/auth.py` | Agregar schemas de Stripe o crear `stripe_schemas.py` |
| `routers/transaction.py` | Usar factory para seleccionar implementación |
| `frontend/Client-UserPY/app/templates/wallet/index.html` | Integrar Stripe Elements (responsive) |
| `frontend/Client-UserPY/app/routers/wallet.py` | Endpoint para crear PaymentIntent client-side |

---

## 2. Switch de Entorno (Punto 1.1)

### 2.1 Configuración en `config.py`

```python
@property
def is_production(self) -> bool:
    """True si ENVIRONMENT=production, False en development"""
    return self.node_env.lower() == "production"

@property
def use_stripe(self) -> bool:
    """Usar Stripe solo en production con credenciales configuradas"""
    return self.is_production and bool(self.stripe_secret_key)
```

### 2.2 Variables de Entorno Requeridas (`.env`)

```bash
# ── Entorno ──────────────────────────────────────────────
ENVIRONMENT=development  # O production

# ── Stripe (TEST) ────────────────────────────────────────
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_API_VERSION=2026-08-26.dahlia
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2.3 Factory Pattern (`payment_gateway_factory.py`)

```python
from app.config import settings

def get_payment_service():
    """Retorna la implementación de pago según entorno"""
    if settings.use_stripe:
        from app.services.transaction_service_Stp import StripePaymentService
        return StripePaymentService()
    else:
        from app.services.transaction_service import SimulationPaymentService
        return SimulationPaymentService()
```

---

## 3. Implementación Stripe (Archivos `-Stp`)

### 3.1 `transaction_service-Stp.py`

**Características clave:**
- ✅ Usa `PaymentMethod` (ej: `pm_card_visa`) — **NUNCA números de tarjeta directos**
- ✅ `PaymentIntent` con `confirm=true`, `allow_redirects=never`
- ✅ Moneda: **GTQ** (Quetzales) — Stripe soporta GTQ desde 2024
- ✅ Manejo de errores específicos de Stripe (CardError, rate_limit, etc.)
- ✅ Metadata con `user_id`, `cui`, `transaction_type` (RECARGA/COMPRA_TARJETA)
- ✅ Idempotency keys para evitar duplicados
- ✅ Webhook handling para `payment_intent.succeeded` / `payment_intent.payment_failed`

**Métodos principales:**
```python
class StripePaymentService:
    async def process_recharge(user_id: str, cui: str, amount: float, payment_method_id: str) -> dict
    async def process_purchase_card(user_id: str, cui: str, payment_method_id: str) -> dict
    async def create_setup_intent(user_id: str) -> str  # Para guardar tarjetas futuras
    async def handle_webhook_event(event: dict) -> dict
```

### 3.2 Schemas Stripe (`schemas/stripe_schemas.py`)

```python
class StripeRechargeRequest(BaseAuthSchema):
    Amount: float = Field(gt=0, validation_alias=AliasChoices("Amount", "amount"))
    PaymentMethodId: str = Field(pattern=r"^pm_", validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"))
    SavePaymentMethod: bool = Field(default=False, validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"))

class StripePurchaseCardRequest(BaseAuthSchema):
    PaymentMethodId: str = Field(pattern=r"^pm_")
    SavePaymentMethod: bool = Field(default=False)

class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: dict
```

---

## 4. Frontend - Stripe Elements Integration (Punto 1.3)

### 4.1 Cambios en `wallet/index.html` (Responsive)

**Tabs actualizados:**
- **Recargar Saldo** → Usa `Stripe Elements` (CardElement) + botón "Pagar con Stripe"
- **Adquirir Tarjeta** → Usa `Stripe Elements` + botón "Comprar con Stripe"
- Mantener UI actual como fallback visual

**JavaScript Stripe:**
```javascript
// Cargar Stripe.js desde CDN
const stripe = Stripe('{{ stripe_publishable_key }}');
const elements = stripe.elements();
const card = elements.create('card', { style: { base: { ... } } });
card.mount('#card-element');

// Al submit: stripe.confirmCardPayment(client_secret, { payment_method: { card } })
```

**Responsive Design (Tailwind):**
- Grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` para formulario
- Card visual `w-full md:w-80` adaptable
- Inputs `w-full px-3 py-2.5` touch-friendly
- Breakpoints: `sm:`, `md:`, `lg:`, `xl:`

### 4.2 Nuevo Endpoint en `wallet.py` (Frontend)

```python
@router.post("/create-payment-intent")
async def create_payment_intent(request: Request, amount: float = Form(...), type: str = Form("recharge")):
    """Crea PaymentIntent en backend y retorna client_secret para Stripe.js"""
    token = request.session.get("token")
    user = await require_auth(request)
    # Llama a Auth-Python /api/transaction/create-payment-intent
    # Retorna { client_secret: "pi_xxx_secret_yyy" }
```

---

## 5. Flujo de Pago Completo

### 5.1 Recarga de Saldo (Production - Stripe)

```
1. Usuario entra a /wallet?tab=recharge
2. Frontend carga Stripe.js + Elements (CardElement)
3. Usuario ingresa monto → Click "Recargar"
4. Frontend POST /wallet/create-payment-intent { amount, type: "recharge" }
5. Backend (Auth-Python):
   - Factory detecta production → usa StripePaymentService
   - StripePaymentService.create_payment_intent(amount, metadata)
   - Retorna client_secret
6. Frontend: stripe.confirmCardPayment(client_secret, { payment_method: { card } })
7. Stripe procesa → Webhook payment_intent.succeeded
8. Backend webhook actualiza wallet + crea factura
9. Frontend redirige a /wallet/{invoiceId} con toast success
```

### 5.2 Compra Tarjeta Ciudadana (Q20.00 fijo)

```
Mismo flujo pero:
- amount = 20.00 fijo
- type = "purchase_card"
- Verifica que usuario no tenga tarjeta (hasCitizenCard)
- Al éxito: hasCitizenCard=true, courtesyTrips=5, balance=20.00
```

### 5.3 Development (Simulación Actual)

```
1. Usuario ingresa tarjeta (4242 4242 4242 4242), expiración, CVV
2. Luhn validation en transaction_service.py
3. asyncio.sleep(1.5) simula latencia
4. add_funds() directo a MongoDB
5. Retorna transactionId simulado
```

---

## 6. Testing Strategy (Punto 2.0)

### 6.1 Credenciales de Prueba Stripe

| Tipo | PaymentMethod ID | Descripción |
|------|------------------|-------------|
| Visa exitosa | `pm_card_visa` | Pago exitoso |
| Mastercard exitosa | `pm_card_mastercard` | Pago exitoso |
| Rechazo genérico | `pm_card_chargeDeclined` | `card_declined` / `generic_decline` |
| Fondos insuficientes | `pm_card_chargeDeclinedInsufficientFunds` | `insufficient_funds` |
| Tarjeta perdida | `pm_card_chargeDeclinedLostCard` | `lost_card` |
| Tarjeta robada | `pm_card_chargeDeclinedStolenCard` | `stolen_card` |
| Tarjeta vencida | `pm_card_chargeDeclinedExpiredCard` | `expired_card` |
| CVC incorrecto | `pm_card_chargeDeclinedIncorrectCvc` | `incorrect_cvc` |
| Error procesamiento | `pm_card_chargeDeclinedProcessingError` | `processing_error` |

### 6.2 Usuario Seed para Testing

**Usuario único con tarjeta válida:** `2000000000002` (Usuario123!)
- Solo este usuario puede usar `pm_card_visa` en tests
- Otros usuarios seed (2000000000001, 2000000000003) → solo simulación

### 6.3 Tests Playwright (`test/test_stripe_integration.py`)

```python
def test_stripe_recharge_success(login_user: Page):
    """Test recarga exitosa con pm_card_visa en production"""
    # Requiere ENVIRONMENT=production y Stripe keys configuradas
    # Usa stripe.confirmCardPayment con pm_card_visa

def test_stripe_recharge_declined(login_user: Page):
    """Test rechazo con pm_card_chargeDeclinedInsufficientFunds"""

def test_simulation_recharge(login_user: Page):
    """Test simulacro actual (development) con Luhn válido 4242424242424242"""

def test_webhook_payment_intent_succeeded():
    """Test webhook handler con event mock"""
```

### 6.4 Comandos de Test Webhook

```bash
# Configurar webhook en Stripe CLI
stripe listen --forward-to localhost:5001/api/stripe/webhook

# Disparar evento de prueba
stripe trigger payment_intent.succeeded

# Verificar en logs: "[Stripe Webhook] PaymentIntent succeeded: pi_xxx"
```

**URL Producción:** `https://tconecta-auth.onrender.com/api/stripe/webhook`
**Versión API:** `2026-08-26.dahlia`

---

## 7. Cambios en Base de Datos / Despliegue

### 7.1 MongoDB (TransmetroUserDb)

**Colección `wallets` - Sin cambios estructurales**
- Los campos existentes (`saldo`, `viajesCortesia`, `hasCitizenCard`, `historialRecargas`) son compatibles
- Stripe guarda `transaction_id` = `payment_intent.id` (ej: `pi_3xxx`)
- Facturas en colección `invoices` ya tienen `transaction_id` string

### 7.2 PostgreSQL (TransmetroAuthDb) - **CAMBIO REQUERIDO**

**Tabla `transmetro_users` - Nuevo campo:**
```sql
ALTER TABLE transmetro_users ADD COLUMN stripe_test_allowed BOOLEAN NOT NULL DEFAULT FALSE;
```

**Seed actualizado:**
- Usuario `2000000000002` (usuario@gmail.com / Usuario123!) → `stripe_test_allowed = TRUE`
- Usuarios `0000000000000`, `1000000000001` → `stripe_test_allowed = FALSE`

**Propósito:** Solo el usuario seed `2000000000002` puede usar PaymentMethods de prueba de Stripe (`pm_card_visa`, `pm_card_mastercard`, etc.) en production. Esto evita que otros usuarios usen tarjetas de prueba en producción.

### 7.3 Variables de Entorno por Servicio

| Servicio | Variables Nuevas/Modificadas |
|----------|------------------------------|
| **Auth-Python** | `ENVIRONMENT=production`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_API_VERSION=2026-08-26.dahlia`, `STRIPE_WEBHOOK_SECRET` |
| **Client-UserPY** | `STRIPE_PUBLISHABLE_KEY` (para frontend) |
| **Client-AdminPY** | Ninguna |
| **Server-AdminPY** | Ninguna |
| **Server-ClientPY** | Ninguna |
| **Mobile** | `STRIPE_PUBLISHABLE_KEY` (si usa wallet) |

### 7.4 Docker / Render Deployment

**Auth-Python (Render):**
```yaml
# render.yaml o dashboard
ENVIRONMENT=production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_API_VERSION=2026-08-26.dahlia
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Webhook URL en Stripe Dashboard:**
```
https://tconecta-auth.onrender.com/api/stripe/webhook
Eventos: payment_intent.succeeded, payment_intent.payment_failed
```

---

## 8. Checklist de Implementación

### Fase 1: Backend Core
- [ ] `config.py` → property `is_production` y `use_stripe`
- [ ] `payment_gateway_factory.py` → factory pattern
- [ ] `transaction_service-Stp.py` → implementación completa Stripe
- [ ] `schemas/stripe_schemas.py` → schemas Stripe
- [ ] `routers/transaction.py` → usar factory
- [ ] `routers/stripe_webhook.py` → mejorar handling (ya existe base)

### Fase 2: Frontend
- [ ] `wallet/index.html` → integrar Stripe Elements (responsive)
- [ ] `wallet.py` (frontend) → endpoint `/create-payment-intent`
- [ ] Cargar `STRIPE_PUBLISHABLE_KEY` en template context

### Fase 3: Testing
- [ ] `test/test_stripe_integration.py` → tests E2E ambos modos
- [ ] Configurar usuario seed con `pm_card_visa`
- [ ] Test webhook con `stripe trigger payment_intent.succeeded`

### Fase 4: Deployment
- [ ] Variables de entorno en Render
- [ ] Configurar webhook en Stripe Dashboard
- [ ] Verificar `JWT_SECRET` idéntico en todos los servicios
- [ ] Probar flujo completo en staging

---

## 9. Referencias y Comandos Útiles

### 9.1 Stripe CLI
```bash
# Instalar
npm i -g @stripe/cli@latest

# Login
stripe login

# Ver webhooks
stripe webhook list

# Forward local
stripe listen --forward-to localhost:5001/api/stripe/webhook

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
stripe trigger setup_intent.succeeded
```

### 9.2 Tarjetas de Prueba (Documentación Oficial)
https://docs.stripe.com/testing?locale=es-419&testing-method=card-numbers

### 9.3 Stripe Elements Docs
https://stripe.com/docs/stripe-js/elements/quickstart

### 9.4 PaymentIntent API
https://stripe.com/docs/api/payment_intents/create

---

## 10. Notas Importantes

1. **PCI Compliance**: Nunca enviar números de tarjeta al backend. Usar `PaymentMethod` IDs (`pm_...`) únicamente.

2. **Moneda GTQ**: Stripe soporta Quetzales Guatemaltecos. Usar `currency="gtq"` y `amount` en centavos (Q20.00 = 2000).

3. **Idempotency**: Usar `idempotency_key` en `PaymentIntent.create` para evitar cargos duplicados por reintentos de red.

4. **Webhook Seguridad**: Siempre verificar `Stripe-Signature` header con `STRIPE_WEBHOOK_SECRET`.

5. **Fallback Development**: Si `ENVIRONMENT=development` o faltan keys Stripe → usar simulación Luhn automáticamente.

6. **Rollback Plan**: Si hay issues en production, cambiar `ENVIRONMENT=development` desactiva Stripe instantáneamente.

---

## 11. Próximos Pasos Inmediatos

1. **Crear archivos `-Stp`** en `backend/Auth-Python/app/services/` ✅
2. **Implementar factory** y actualizar `config.py` ✅
3. **Modificar router** `transaction.py` para usar factory ✅
4. **Integrar Stripe Elements** en frontend wallet template ✅
5. **Escribir tests** Playwright para ambos flujos ✅
6. **Configurar webhook** en Stripe Dashboard con URL de producción
7. **Deploy a staging** y validar flujo completo

---

## 12. Pasos de Testing Webhook (Para Verificación Manual)

### 12.1 Configurar Stripe CLI Local
```bash
# Instalar Stripe CLI
npm i -g @stripe/cli@latest

# Login a Stripe
stripe login

# Forward webhook a local
stripe listen --forward-to localhost:5001/api/stripe/webhook
# Copiar el webhook signing secret que genera (whsec_...) y poner en .env
```

### 12.2 Probar Webhook payment_intent.succeeded
```bash
# En otra terminal, con Stripe CLI corriendo:
stripe trigger payment_intent.succeeded

# Verificar en logs del backend:
# [Stripe Webhook] Event: payment_intent.succeeded | Result: {'status': 'processed', ...}
```

### 12.3 Probar Webhook payment_intent.payment_failed
```bash
stripe trigger payment_intent.payment_failed

# Verificar en logs:
# [Stripe Webhook] Event: payment_intent.payment_failed | Result: {'status': 'payment_failed', ...}
```

### 12.4 Configurar Webhook en Stripe Dashboard (Producción)
1. Ir a https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. URL: `https://tconecta-auth.onrender.com/api/stripe/webhook`
4. Eventos a escuchar:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
   - `setup_intent.succeeded`
5. Versión API: `2026-08-26.dahlia`
6. Copiar `Signing secret` (whsec_...) → variable `STRIPE_WEBHOOK_SECRET`

---

## 13. Checklist de Deployment (Producción)

### 13.1 Base de Datos
- [ ] Ejecutar migración: `ALTER TABLE transmetro_users ADD COLUMN stripe_test_allowed BOOLEAN NOT NULL DEFAULT FALSE;`
- [ ] Actualizar usuario seed: `UPDATE transmetro_users SET stripe_test_allowed = TRUE WHERE cui = '2000000000002';`

### 13.2 Variables de Entorno (Render - Auth-Python)
- [ ] `ENVIRONMENT=production`
- [ ] `STRIPE_SECRET_KEY=sk_live_...` (clave secreta LIVE)
- [ ] `STRIPE_PUBLISHABLE_KEY=pk_live_...` (clave pública LIVE)
- [ ] `STRIPE_API_VERSION=2026-08-26.dahlia`
- [ ] `STRIPE_WEBHOOK_SECRET=whsec_...` (del Stripe Dashboard)
- [ ] `JWT_SECRET=A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345` (idéntico en todos los servicios)

### 13.3 Variables de Entorno (Render - Client-UserPY)
- [ ] `STRIPE_PUBLISHABLE_KEY=pk_live_...` (misma que Auth-Python)

### 13.4 Verificaciones Post-Deploy
- [ ] Health check: `https://tconecta-auth.onrender.com/api/health`
- [ ] Webhook accesible: `https://tconecta-auth.onrender.com/api/stripe/webhook` (POST 400 sin signature = OK)
- [ ] Login usuario `2000000000002` → Wallet → Ver Stripe Elements cargado
- [ ] Test recarga con `pm_card_visa` → Éxito
- [ ] Test compra tarjeta con `pm_card_visa` → Éxito
- [ ] Test usuario `1000000000001` → Wallet → Error "no autorizado para tarjetas de prueba"
- [ ] Verificar facturas creadas en MongoDB

---

## 14. Rollback Plan

Si hay issues críticos en production:

1. **Inmediato:** Cambiar `ENVIRONMENT=development` en Auth-Python → Desactiva Stripe, usa simulación Luhn
2. **Variables:** Quitar `STRIPE_SECRET_KEY` y `STRIPE_PUBLISHABLE_KEY` de Render
3. **Frontend:** Quitar `STRIPE_PUBLISHABLE_KEY` de Client-UserPY
4. **Webhook:** Desactivar endpoint en Stripe Dashboard
5. **DB:** No requiere rollback (campo `stripe_test_allowed` no afecta simulación)

---

*Documento generado para TConectaPY — Clean Architecture Stripe Integration*
*Versión: 1.0 | Fecha: 2026-10-06*