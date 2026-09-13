import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/TransmetroAdminDb")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
    )
    db = client.get_database()
    await client.admin.command("ping")
    print(f"[DB] Conectado a MongoDB: {MONGODB_URI}")


async def close_db():
    global client
    if client:
        client.close()
        print("[DB] Conexion MongoDB cerrada")


def get_db():
    return db
