from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    UNDERMINE_API_KEY: str = ""
    WOW_REGION: str = "eu"
    DATABASE_URL: str = "postgresql+asyncpg://wow_user:wow_password@db:5432/wow_market"
    COLLECTOR_INTERVAL_HOURS: int = 1

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
