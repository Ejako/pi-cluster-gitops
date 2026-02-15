import os # for environmental variables, instead of hard coding
from typing import Optional

class Config:
    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: int = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "stocks")
    
    # Application configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENV: str = os.getenv("ENV", "development")

    # Other to be included

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration on startup"""
        if cls.ENV not in ("development", "staging", "production"):
            raise ValueError(f"Invalid ENV: {cls.ENV}")
        if cls.DB_PASSWORD == "password" and cls.ENV == "production":
            raise ValueError("Default DB_PASSWORD used in production!")
        
    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
