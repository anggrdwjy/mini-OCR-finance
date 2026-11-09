from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ocruser:ubah_ini@db:5432/ocr_finance"
    JWT_SECRET: str = "secret_acak_panjang_minimal_32_karakter"
    JWT_EXPIRE_HOURS: int = 24
    OCR_PROVIDER: str = "tesseract"
    OCR_API_KEY: str = ""
    UPLOAD_DIR: str = "/app/uploads"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
