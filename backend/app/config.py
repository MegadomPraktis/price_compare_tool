import os
from pydantic_settings import BaseSettings  # <-- pydantic v2

class Settings(BaseSettings):
    APP_NAME: str = "PriceCompare"
    APP_ENV: str = os.getenv("APP_ENV", "dev")

    # SQL Server DSN
    MSSQL_DSN: str = os.getenv(
        "MSSQL_DSN",
        "mssql+pyodbc://USER:PASS@HOST:1433/pricecompare?driver=ODBC+Driver+17+for+SQL+Server",
    )

    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER: str | None = os.getenv("SMTP_USER")
    SMTP_PASS: str | None = os.getenv("SMTP_PASS")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "no-reply@pricecompare.local")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    # Optional: automatically read a .env file in /backend
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()
