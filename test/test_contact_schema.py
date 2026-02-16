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