from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_database()
    print(f"[TransmetroAuth] MongoDB conectado: {client.address}")


async def close_mongo():
    global client
    if client:
        client.close()
        print("[TransmetroAuth] MongoDB desconectado")


def get_mongo_db():
    return db
