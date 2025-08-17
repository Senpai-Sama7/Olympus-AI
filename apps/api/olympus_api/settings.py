import os
import threading
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    # Common
    ENV: str = Field(default="dev")
    UVICORN_HOST: str = Field(default="0.0.0.0")
    UVICORN_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    # CORS
    DEV_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    PROD_ALLOWED_ORIGINS: List[str] = Field(default_factory=list)
    CORS_ALLOWED_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    CORS_ALLOWED_HEADERS: List[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type", "X-Request-ID"]
    )
    CORS_MAX_AGE: int = Field(default=600)

    # Timeouts & body size
    REQUEST_TIMEOUT_SEC: int = Field(default=30)
    CONNECT_TIMEOUT_SEC: int = Field(default=10)
    MAX_BODY_BYTES: int = Field(default=5_000_000)

    # Rate limits (per-IP)
    RATE_LIMIT_GLOBAL_PER_MIN: int = Field(default=120)
    RATE_LIMIT_CHAT_PER_MIN: int = Field(default=30)

    # Paths & sandbox
    SANDBOX_ROOT: str = Field(default=".sandbox")
    ALLOW_WRITE_DIRS: List[str] = Field(default_factory=lambda: [".sandbox"])
    DB_PATH: str = Field(default=".data/olympus.db")
    WORKER_HEARTBEAT_PATH: str = Field(default=".sandbox/.status/worker.json")

    # LLM (Ollama)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL_ALLOWLIST: List[str] = Field(
        default_factory=lambda: ["llama3:8b", "llama3.1:8b"]
    )
    # LLM backend toggle
    OLY_LLM_BACKEND: str = Field(default="ollama")  # or 'llamacpp'
    LLAMA_CPP_URL: str = Field(default="http://127.0.0.1:8080")
    LLAMA_CPP_MODEL_DIR: str = Field(default=os.environ.get("LLAMA_CPP_MODEL_DIR", "/home/donovan/Documents/LocalLLMs"))

    # Metrics
    METRICS_ENABLED: bool = Field(default=True)

    def as_redacted_dict(self) -> dict:
        data = self.model_dump()
        # No secrets in this config; retain values as-is for transparency
        return data


_singleton: Optional[Settings] = None
_lock = threading.Lock()


def _parse_list(env_value: Optional[str]) -> List[str]:
    if not env_value:
        return []
    return [item.strip() for item in env_value.split(",") if item.strip()]


def _load_env_if_needed() -> None:
    # Auto-load .env in dev/test to support local runs
    if os.environ.get("ENV", "dev") in ("dev", "test"):
        # Load .env if present; ignore if missing
        load_dotenv(override=False)


def _coerce_positive_int(value: Optional[str], default: int) -> int:
    try:
        v = int(value) if value is not None else default
        return v if v > 0 else default
    except Exception:
        return default


def get_settings() -> Settings:
    global _singleton
    if _singleton is not None:
        return _singleton
    with _lock:
        if _singleton is not None:
            return _singleton
        _load_env_if_needed()
        try:
            settings = Settings(
                ENV=os.environ.get("ENV", "dev"),
                UVICORN_HOST=os.environ.get("UVICORN_HOST", "0.0.0.0"),
                UVICORN_PORT=_coerce_positive_int(os.environ.get("UVICORN_PORT"), 8000),
                LOG_LEVEL=os.environ.get("LOG_LEVEL", "INFO"),
                DEV_ALLOWED_ORIGINS=_parse_list(os.environ.get("DEV_ALLOWED_ORIGINS"))
                or [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ],
                PROD_ALLOWED_ORIGINS=_parse_list(
                    os.environ.get("PROD_ALLOWED_ORIGINS")
                ),
                CORS_ALLOWED_METHODS=_parse_list(os.environ.get("CORS_ALLOWED_METHODS"))
                or [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "OPTIONS",
                ],
                CORS_ALLOWED_HEADERS=_parse_list(os.environ.get("CORS_ALLOWED_HEADERS"))
                or [
                    "Authorization",
                    "Content-Type",
                    "X-Request-ID",
                ],
                CORS_MAX_AGE=_coerce_positive_int(os.environ.get("CORS_MAX_AGE"), 600),
                REQUEST_TIMEOUT_SEC=_coerce_positive_int(
                    os.environ.get("REQUEST_TIMEOUT_SEC"), 30
                ),
                CONNECT_TIMEOUT_SEC=_coerce_positive_int(
                    os.environ.get("CONNECT_TIMEOUT_SEC"), 10
                ),
                MAX_BODY_BYTES=_coerce_positive_int(
                    os.environ.get("MAX_BODY_BYTES"), 5_000_000
                ),
                RATE_LIMIT_GLOBAL_PER_MIN=_coerce_positive_int(
                    os.environ.get("RATE_LIMIT_GLOBAL_PER_MIN"), 120
                ),
                RATE_LIMIT_CHAT_PER_MIN=_coerce_positive_int(
                    os.environ.get("RATE_LIMIT_CHAT_PER_MIN"), 30
                ),
                SANDBOX_ROOT=os.environ.get("SANDBOX_ROOT", ".sandbox"),
                ALLOW_WRITE_DIRS=_parse_list(os.environ.get("ALLOW_WRITE_DIRS"))
                or [".sandbox"],
                DB_PATH=os.environ.get("DB_PATH", ".data/olympus.db"),
                WORKER_HEARTBEAT_PATH=os.environ.get(
                    "WORKER_HEARTBEAT_PATH", ".sandbox/.status/worker.json"
                ),
                OLLAMA_BASE_URL=os.environ.get(
                    "OLLAMA_BASE_URL", "http://localhost:11434"
                ),
                OLLAMA_MODEL_ALLOWLIST=_parse_list(
                    os.environ.get("OLLAMA_MODEL_ALLOWLIST")
                )
                or ["llama3:8b", "llama3.1:8b"],
                OLY_LLM_BACKEND=os.environ.get("OLY_LLM_BACKEND", "ollama"),
                LLAMA_CPP_URL=os.environ.get("LLAMA_CPP_URL", "http://127.0.0.1:8080"),
                METRICS_ENABLED=os.environ.get("METRICS_ENABLED", "true").lower()
                in ("1", "true", "yes", "y"),
            )
        except ValidationError:
            # Fallback to defaults if validation fails
            settings = Settings()
        _singleton = settings
        return settings
