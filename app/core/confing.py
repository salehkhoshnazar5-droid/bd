import os
from dotenv import load_dotenv
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Tuple



load_dotenv()

ADMIN_LOGIN_PASSWORD = os.getenv("ADMIN_LOGIN_PASSWORD")

if not ADMIN_LOGIN_PASSWORD:
    raise ValueError("ADMIN_LOGIN_PASSWORD environment variable is not set.")

def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: Optional[str], default: Tuple[str, ...]) -> Tuple[str, ...]:
    if value is None:
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return tuple(items) if items else default


@dataclass(frozen=True)
class Settings:
    database_url: str
    sql_echo: bool
    cors_allow_origins: Tuple[str, ...]
    cors_allow_credentials: bool
    cors_allow_methods: Tuple[str, ...]
    cors_allow_headers: Tuple[str, ...]
    secret_key: str
    access_token_expire_minutes: int
    admin_login_password: str
    cookie_secure: bool
    log_level: str
    geo_restriction_enabled: bool
    geo_allow_iran_only: bool
    enforce_browser_only: bool
    trusted_country_header: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    admin_login_password = os.getenv("ADMIN_LOGIN_PASSWORD")
    if not admin_login_password:
        raise ValueError("ADMIN_LOGIN_PASSWORD environment variable is not set.")

    access_token_expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    try:
        access_token_expire_minutes = int(access_token_expire_minutes)
    except ValueError:
        raise ValueError(f"ACCESS_TOKEN_EXPIRE_MINUTES must be an integer, got {access_token_expire_minutes}.")

    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./basij.db"),
        sql_echo=_parse_bool(os.getenv("SQL_ECHO"), False),
        cors_allow_origins=_parse_csv(os.getenv("CORS_ALLOW_ORIGINS"), ("http://kerman_bd", "http://127.0.0.1", "http://localhost")),
        cors_allow_credentials=_parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), True),
        cors_allow_methods=_parse_csv(os.getenv("CORS_ALLOW_METHODS"), ("*",)),
        cors_allow_headers=_parse_csv(os.getenv("CORS_ALLOW_HEADERS"), ("*",)),
        secret_key=os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY"),
        access_token_expire_minutes=access_token_expire_minutes,
        admin_login_password=admin_login_password,
        cookie_secure=_parse_bool(os.getenv("COOKIE_SECURE"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        geo_restriction_enabled=_parse_bool(os.getenv("GEO_RESTRICTION_ENABLED"), False),
        geo_allow_iran_only=_parse_bool(os.getenv("GEO_ALLOW_IRAN_ONLY"), True),
        enforce_browser_only=_parse_bool(os.getenv("ENFORCE_BROWSER_ONLY"), True),
        trusted_country_header=os.getenv("TRUSTED_COUNTRY_HEADER", "CF-IPCountry"),
    )


settings = get_settings()
