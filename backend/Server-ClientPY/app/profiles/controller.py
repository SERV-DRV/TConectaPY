from datetime import datetime, timezone

from fastapi import HTTPException

from app.configs.database import get_db
from app.profiles.model import ProfileResponse


def _serialize(doc: dict) -> dict:
    doc["userId"] = doc.pop("_id")
    doc.pop("isActive", None)
    created = doc.pop("created_at", None)
    updated = doc.pop("updated_at", None)
    if created:
        doc["createdAt"] = created.isoformat() if isinstance(created, datetime) else str(created)
    if updated:
        doc["updatedAt"] = updated.isoformat() if isinstance(updated, datetime) else str(updated)
    return doc


async def get_profile(user_id: str) -> dict:
    db = get_db()
    profile = await db.profiles.find_one({"_id": user_id})
    if not profile:
        now = datetime.now(timezone.utc)
        new_profile = {
            "_id": user_id,
            "fullName": "",
            "preferredLanguage": "es",
            "frequentRoutes": [],
            "isActive": True,
            "created_at": now,
            "updated_at": now,
        }
        await db.profiles.insert_one(new_profile)
        return _serialize(new_profile)
    return _serialize(profile)


async def update_profile(user_id: str, data: dict) -> dict:
    db = get_db()
    update_fields = {k: v for k, v in data.items() if v is not None}
    update_fields["updated_at"] = datetime.now(timezone.utc)

    await db.profiles.update_one(
        {"_id": user_id},
        {"$set": update_fields},
        upsert=True,
    )

    profile = await db.profiles.find_one({"_id": user_id})
    return _serialize(profile)
