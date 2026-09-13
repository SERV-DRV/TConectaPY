import os

from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/TransmetroUserDb")
    client = AsyncIOMotorClient(uri)
    db = client.get_database()
    print(f"[DB] Conectado a MongoDB: {client.address}")


async def close_db():
    global client
    if client:
        client.close()
        print("[DB] Conexión MongoDB cerrada")


def get_db():
    return db
