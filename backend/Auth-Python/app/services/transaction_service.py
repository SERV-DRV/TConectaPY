import asyncio
import uuid

from app.helpers.luhn import is_valid_luhn
from app.services.wallet_integration import add_funds, has_citizen_card, initialize_wallet


async def process_payment(user_id: str, card_number: str, amount: float) -> dict:
    if not is_valid_luhn(card_number):
        return {"isSuccess": False, "message": "Número de tarjeta inválida.", "transactionId": ""}

    await asyncio.sleep(1.5)

    wallet_updated = await add_funds(user_id, amount)

    if not wallet_updated:
        return {
            "isSuccess": False,
            "message": "Transacción aprobada, pero falló la sincronización con la billetera.",
            "transactionId": "",
        }

    return {
        "isSuccess": True,
        "message": "Recarga procesada exitosamente.",
        "transactionId": str(uuid.uuid4()),
    }


async def purchase_card(user_id: str, card_number: str, amount: float) -> dict:
    if amount != 20.00:
        return {
            "isSuccess": False,
            "message": "El costo de emisión de la Tarjeta Ciudadana es exactamente Q20.00.",
            "transactionId": "",
        }

    if not is_valid_luhn(card_number):
        return {"isSuccess": False, "message": "Número de tarjeta inválida.", "transactionId": ""}

    already_has_card = await has_citizen_card(user_id)
    if already_has_card:
        return {
            "isSuccess": False,
            "message": "Transacción denegada. El usuario ya posee una Tarjeta Ciudadana activa.",
            "transactionId": "",
        }

    await asyncio.sleep(1.5)

    wallet_initialized = await initialize_wallet(user_id)

    if not wallet_initialized:
        return {
            "isSuccess": False,
            "message": "Transacción aprobada, pero falló la creación de la billetera. Contacte soporte.",
            "transactionId": "",
        }

    return {
        "isSuccess": True,
        "message": "Tarjeta Ciudadana adquirida exitosamente. Se han acreditado Q20.00 de saldo y 5 viajes de cortesía.",
        "transactionId": str(uuid.uuid4()),
    }
