from datetime import datetime, timezone
from typing import Optional

from app.database_mongo import get_mongo_db
from bson import ObjectId


async def create_invoice(
    user_id: str,
    cui: str,
    tipo: str,  # "RECARGA" | "COMPRA_TARJETA"
    monto: float,
    tarjeta_ultimos4: str,
    transaction_id: str,
) -> Optional[str]:
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
            "totalPages": total_pages,
        }
    except Exception as e:
        print(f"[InvoiceService] Error obteniendo facturas: {e}")
        return {"invoices": [], "total": 0, "page": 1, "limit": limit, "totalPages": 1}


async def get_invoice_by_id(invoice_id: str, user_id: str) -> Optional[dict]:
    """
    Obtiene factura por ID verificando ownership.
    """
    try:
        mongo_db = get_mongo_db()
        invoice = await mongo_db.invoices.find_one({
            "_id": ObjectId(invoice_id),
            "userId": user_id,
        })
        if invoice:
            invoice["_id"] = str(invoice["_id"])
            invoice["fecha"] = invoice["fecha"].isoformat() if hasattr(invoice["fecha"], "isoformat") else str(invoice["fecha"])
        return invoice
    except Exception as e:
        print(f"[InvoiceService] Error obteniendo factura: {e}")
        return None