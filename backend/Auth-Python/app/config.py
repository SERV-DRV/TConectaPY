from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Aplicación ──────────────────────────────────────
    node_env: str = "development"
    port: int = 5001

    # ── PostgreSQL ─────────────────────────────────────
    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "TransmetroAuthDb"
    db_username: str = "postgres"
    db_password: str = "postgres"

    # ── JWT ────────────────────────────────────────────
    jwt_secret: str = "A_SUPER_SECRET_KEY_FOR_TRANSMETRO_CONECTA_12345"
    jwt_issuer: str = "TransmetroAuthServer"
    jwt_audience: str = "TransmetroUsers"
    jwt_expires_in: int = 120  # minutos
    jwt_reset_expires_in: int = 15  # minutos

    # ── MongoDB (Wallets — TransmetroUserDb) ──────────
    mongodb_uri: str = "mongodb://localhost:27017/TransmetroUserDb"

    # ── CORS ───────────────────────────────────────────
    allowed_origins: str = ""

    # ── Rate Limiting ──────────────────────────────────
    rate_limit_window: int = 60  # segundos
    rate_limit_max: int = 100
    auth_rate_limit_max: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.allowed_origins:
            return []
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_database_url(self) -> str:
        """URL síncrona para create_all (no requiere asyncpg)."""
        if self.database_url:
            return self.database_url.replace("+asyncpg", "")
        return (
            f"postgresql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
