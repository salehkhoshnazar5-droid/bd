from app.core.geo_access import is_iran_country, looks_like_browser, parse_client_ip


def test_parse_client_ip_uses_first_valid_forwarded_ip():
    assert parse_client_ip("198.51.100.1, 10.0.0.2", "127.0.0.1") == "198.51.100.1"


def test_parse_client_ip_falls_back_to_remote_addr_when_forwarded_invalid():
    assert parse_client_ip("unknown", "203.0.113.44") == "203.0.113.44"


def test_parse_client_ip_returns_none_when_no_valid_ip():
    assert parse_client_ip("bad-value", "also-bad") is None


def test_looks_like_browser_accepts_common_user_agents():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
    assert looks_like_browser(ua)


def test_looks_like_browser_rejects_non_browser_clients():
    assert not looks_like_browser("python-requests/2.31.0")


def test_is_iran_country_matches_ir_case_insensitive():
    assert is_iran_country("ir")
    assert not is_iran_country("DE")