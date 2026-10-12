from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lenny Growth Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Postgres
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    # Agent & LLM Configuration
    AGENT_PROVIDER: str = "ollama"
    AGENT_MODEL: str = "qwen3:4b"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    ANTHROPIC_API_KEY: str | None = None
    AGENT_TIMEOUT_SECONDS: float = 120.0
    AGENT_TOP_K: int = 5

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
