from pathlib import Path

import pytest
from starlette.datastructures import FormData
from app.core.json_utils import make_json_safe
from app.core.validators import validate_national_code, validate_student_number


def test_validate_national_code_accepts_exact_10_digits():
    assert validate_national_code("0123456789") == "0123456789"


def test_validate_national_code_normalizes_persian_digits_and_spaces():
    assert validate_national_code("۰۱۲ ۳۴۵-۶۷۸۹") == "0123456789"


def test_validate_national_code_rejects_short_input_instead_of_zero_padding():
    with pytest.raises(ValueError, match="کد ملی باید 10 رقم باشد"):
        validate_national_code("123456789")


def test_validate_student_number_accepts_exact_9_digits():
    assert validate_student_number("123456789") == "123456789"


def test_validate_student_number_rejects_short_input_instead_of_zero_padding():
    with pytest.raises(ValueError, match="شماره دانشجویی باید 9 رقم باشد"):
        validate_student_number("12345678")


def test_login_template_uses_html_pattern_for_exact_digits_without_escaped_backslashes():
    template = Path("app/templates/auth/login.html").read_text(encoding="utf-8")

    assert 'name="national_code"' in template
    assert 'pattern="[0-9]{10}"' in template
    assert 'minlength="10"' in template
    assert 'maxlength="10"' in template

    assert 'name="password"' in template
    assert 'pattern="[0-9]{9}"' in template
    assert 'minlength="9"' in template
    assert 'maxlength="9"' in template

    assert '\\\\d{10}' not in template
    assert '\\\\d{9}' not in template


def test_make_json_safe_converts_bytes_to_text_for_validation_responses():
    assert make_json_safe(b"hello") == "hello"


def test_make_json_safe_handles_nested_bytes_payloads():
    payload = {
        "raw": b"\xd8\xa7\xd8\xaf\xd9\x85\xdb\x8c\xd9\x86",
        "items": [b"one", {"two": b"2"}],
    }

    converted = make_json_safe(payload)

    assert converted["raw"] == "ادمین"
    assert converted["items"][0] == "one"
    assert converted["items"][1]["two"] == "2"

    def test_make_json_safe_converts_formdata_to_plain_dict():
        form_data = FormData([("national_code", "0123456789"), ("password", "123456789")])

        converted = make_json_safe(form_data)

        assert converted == {
            "national_code": "0123456789",
            "password": "123456789",
        }

    def test_admin_ui_does_not_register_conflicting_admin_login_route():
        router_source = Path("app/routers/admin_ui.py").read_text(encoding="utf-8")

        assert '@router.get("/admin/login"' not in router_source
        assert '@router.post("/admin/login")' not in router_source