from typing import Dict, List

from .settings import Settings


def build_cors_kwargs(settings: Settings) -> Dict:
    origins: List[str] = (
        settings.DEV_ALLOWED_ORIGINS
        if settings.ENV == "dev"
        else settings.PROD_ALLOWED_ORIGINS
    )
    return {
        "allow_origins": origins,
        "allow_methods": settings.CORS_ALLOWED_METHODS,
        "allow_headers": settings.CORS_ALLOWED_HEADERS,
        "allow_credentials": False,
        "max_age": settings.CORS_MAX_AGE,
    }
