import pytest
from pydantic import ValidationError

from app.schemas.contact import Contact


def test_contact_requires_name() -> None:
    with pytest.raises(ValidationError):
        Contact()


def test_contact_name_must_be_string() -> None:
    with pytest.raises(ValidationError):
        Contact(name=None)


def test_contact_accepts_valid_name() -> None:
    contact = Contact(name="Ada Lovelace")
    assert contact.name == "Ada Lovelace"


def test_contact_validates_optional_fields() -> None:
    contact = Contact(name="API Team", url="https://example.com", email="team@example.com")
    assert str(contact.url) == "https://example.com"
    assert contact.email == "team@example.com"


def test_contact_allows_extra_fields() -> None:
    contact = Contact(name="API Team", x_slack="#platform")
    assert contact.dict()["x_slack"] == "#platform"