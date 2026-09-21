from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    GROQ_API_KEY: str
    APIFY_API_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
