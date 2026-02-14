from __future__ import annotations

from ipaddress import ip_address
from typing import Optional


BROWSER_SIGNATURES = (
    "Mozilla/5.0",
    "Chrome/",
    "Firefox/",
    "Safari/",
    "Edg/",
)


def parse_client_ip(x_forwarded_for: Optional[str], remote_addr: Optional[str]) -> Optional[str]:
    """Return first valid client IP from forwarding chain or remote address."""
    if x_forwarded_for:
        for candidate in [item.strip() for item in x_forwarded_for.split(",")]:
            if _is_valid_ip(candidate):
                return candidate

    if remote_addr and _is_valid_ip(remote_addr):
        return remote_addr
    return None


def looks_like_browser(user_agent: str) -> bool:
    """Very small heuristic to block non-browser clients when needed."""
    return any(signature in user_agent for signature in BROWSER_SIGNATURES)


def is_iran_country(country_code: Optional[str]) -> bool:
    if not country_code:
        return False
    return country_code.strip().upper() == "IR"


def _is_valid_ip(value: str) -> bool:
    try:
        ip_address(value)
        return True
    except ValueError:
        return False