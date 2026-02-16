import pytest

from app.core.version_checks import validate_runtime_compatibility


def test_rejects_fastapi_with_pydantic_v2() -> None:
    with pytest.raises(RuntimeError, match="FastAPI < 0.100 requires Pydantic < 2.0"):
        validate_runtime_compatibility(
            python_version=(3, 11, 9),
            fastapi_version="0.80.0",
            pydantic_version="2.10.1",
        )


def test_rejects_python_314_with_pydantic_v1() -> None:
    with pytest.raises(RuntimeError, match="Python 3.14 is not supported by Pydantic 1.x"):
        validate_runtime_compatibility(
            python_version=(3, 14, 0),
            fastapi_version="0.80.0",
            pydantic_version="1.10.2",
        )


def test_accepts_known_good_combo() -> None:
    validate_runtime_compatibility(
        python_version=(3, 11, 9),
        fastapi_version="0.80.0",
        pydantic_version="1.10.2",
    )