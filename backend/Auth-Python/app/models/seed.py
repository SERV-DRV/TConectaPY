from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.helpers.password import hash_password
from app.models.user import User

SEED_USERS = [
    {
        "cui": "0000000000000",
        "email": "admin@gmail.com",
        "password": "AdminTransmetro2026!",
        "role": "Admin",
    },
    {
        "cui": "1000000000001",
        "email": "admin2@gmail.com",
        "password": "Admin123!",
        "role": "Admin",
    },
    {
        "cui": "2000000000002",
        "email": "usuario@gmail.com",
        "password": "Usuario123!",
        "role": "User",
    },
]


async def seed_database() -> None:
    """Inserta usuarios semilla si la tabla está vacía."""
    async with async_session_factory() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        for data in SEED_USERS:
            user = User(
                cui=data["cui"],
                email=data["email"],
                password_hash=await hash_password(data["password"]),
                role=data["role"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(user)

        await session.commit()
        print("[TransmetroAuth] Seeder | 3 usuarios semilla insertados.")
