from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from the environment.
    """
    GOOGLE_API_KEY: str
    ALPHAVANTAGE_API_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Create a single, reusable instance of the settings
settings = Settings()
