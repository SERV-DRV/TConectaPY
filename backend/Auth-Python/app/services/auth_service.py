from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.helpers.jwt import (
    generate_access_token,
    generate_password_reset_token,
    validate_password_reset_token,
)
from app.helpers.password import hash_password, verify_password
from app.models.user import User


async def register(cui: str, email: str, password: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.cui == cui))
        if result.scalar_one_or_none():
            raise ValueError("El CUI ya está registrado.")

        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("El correo ya está en uso.")

        user = User(
            cui=cui,
            email=email,
            password_hash=await hash_password(password),
            role="User",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.flush()
        await session.commit()

        token = generate_access_token(user.id, user.cui, user.role)
        return {"token": token, "userId": user.id, "role": user.role}


async def login(cui: str, password: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.cui == cui))
        user = result.scalar_one_or_none()

        if not user or not await verify_password(password, user.password_hash):
            raise ValueError("Credenciales inválidas.")

        token = generate_access_token(user.id, user.cui, user.role)
        return {"token": token, "userId": user.id, "role": user.role}


async def request_password_reset(email: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Usuario no encontrado.")

        token = generate_password_reset_token(user.id, user.email)
        return {"message": "Token generado exitosamente.", "token": token}


async def reset_password(email: str, token: str, new_password: str) -> None:
    if not validate_password_reset_token(token, email):
        raise ValueError("Token inválido o expirado.")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Usuario no encontrado.")

        user.password_hash = await hash_password(new_password)
        await session.flush()
        await session.commit()


async def get_all_users() -> list[dict]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.asc())
        )
        users = result.scalars().all()

        return [
            {
                "id": u.id,
                "cui": u.cui,
                "email": u.email,
                "role": u.role,
                "isActive": u.is_active,
                "createdAt": u.created_at.isoformat(),
            }
            for u in users
        ]


async def register_admin(cui: str, email: str, password: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.cui == cui))
        if result.scalar_one_or_none():
            raise ValueError("El CUI ya está registrado.")

        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("El correo ya está en uso.")

        user = User(
            cui=cui,
            email=email,
            password_hash=await hash_password(password),
            role="Admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.flush()
        await session.commit()

        token = generate_access_token(user.id, user.cui, user.role)
        return {"token": token, "userId": user.id, "role": user.role}


async def get_user_email(user_id: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Usuario no encontrado.")

        return {"email": user.email}


async def update_email(user_id: str, new_email: str) -> dict:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Usuario no encontrado.")

        result = await session.execute(select(User).where(User.email == new_email))
        if result.scalar_one_or_none():
            raise ValueError("Este correo ya está en uso por otra cuenta.")

        user.email = new_email
        await session.flush()
        await session.commit()

        return {"message": "Correo electrónico actualizado exitosamente.", "email": new_email}
