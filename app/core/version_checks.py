from __future__ import annotations

import sys
from typing import Optional, Tuple

import fastapi
import pydantic

VersionTuple = Tuple[int, int, int]


def _parse_version_prefix(version: str, parts: int = 3) -> VersionTuple:
    """Parse a semantic version prefix like `1.10.2` into an integer tuple."""
    values = []
    for token in version.split(".")[:parts]:
        digits = "".join(ch for ch in token if ch.isdigit())
        values.append(int(digits) if digits else 0)

    while len(values) < parts:
        values.append(0)

    return tuple(values)  # type: ignore[return-value]


def validate_runtime_compatibility(
    *,
    python_version: Optional[Tuple[int, int, int]] = None,
    fastapi_version: Optional[str] = None,
    pydantic_version: Optional[str] = None,
) -> None:
    """Raise a clear error for known-incompatible runtime combinations."""

    py_version = python_version or sys.version_info[:3]
    fa_version = _parse_version_prefix(fastapi_version or fastapi.__version__)
    pd_version = _parse_version_prefix(pydantic_version or pydantic.__version__)

    # FastAPI < 0.100 uses Pydantic v1 internals and cannot run on Pydantic v2.
    if fa_version < (0, 100, 0) and pd_version >= (2, 0, 0):
        raise RuntimeError(
            "Incompatible dependency versions detected: FastAPI < 0.100 requires "
            "Pydantic < 2.0. Install pydantic==1.10.2 (or any 1.10.x) when using "
            "fastapi==0.80.0."
        )

    # Pydantic 1.x is not compatible with Python 3.14.
    if pd_version < (2, 0, 0) and py_version >= (3, 14, 0):
        raise RuntimeError(
            "Python 3.14 is not supported by Pydantic 1.x. This can surface as "
            "`ConfigError: unable to infer type for attribute \"name\"` when FastAPI "
            "imports OpenAPI models. Use Python 3.10/3.11 with FastAPI 0.80 + "
            "Pydantic 1.10.x, or upgrade to FastAPI >= 0.115 and Pydantic >= 2."
        )