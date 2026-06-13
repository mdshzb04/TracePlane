from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

_INSECURE_SECRET = "change-me-to-a-secure-random-string-in-production"


class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://agentops:agentops@localhost:5432/agentops_hub"
    DATABASE_URL_SYNC: str = "postgresql://agentops:agentops@localhost:5432/agentops_hub"
    SECRET_KEY: str = _INSECURE_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOW_REGISTRATION: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_PUBLIC_URL: str = "http://127.0.0.1:8000"

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = ""
    GITHUB_OAUTH_ENABLED: bool = False

    # Multi-provider LLM layer (openai | nvidia)
    LLM_PROVIDER: str = "nvidia"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Langfuse observability (LANGFUSE_BASE_URL is the official env var name)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "LANGFUSE_HOST"),
    )
    LANGFUSE_ENABLED: bool = True
    LANGFUSE_TRACING_ENVIRONMENT: str = Field(default="development")

    # Production infrastructure
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_ENABLED: bool = False

    # Resend email delivery
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "Traceplane <onboarding@resend.dev>"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def resend_configured(self) -> bool:
        return bool(self.RESEND_API_KEY.strip())

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def github_oauth_configured(self) -> bool:
        return bool(self.GITHUB_OAUTH_ENABLED and self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET)

    @property
    def github_callback_url(self) -> str:
        if self.GITHUB_REDIRECT_URI.strip():
            return self.GITHUB_REDIRECT_URI.strip()
        # Dev default: callback via Next.js /api proxy so OAuth state cookie stays same-origin
        if self.ENV == "development":
            return f"{self.FRONTEND_URL.rstrip('/')}/api/auth/github/callback"
        return f"{self.BACKEND_PUBLIC_URL.rstrip('/')}/api/v1/auth/github/callback"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENV != "development":
            if self.SECRET_KEY == _INSECURE_SECRET or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be a secure random string of at least 32 characters "
                    "in non-development environments"
                )
        return self


settings = Settings()
