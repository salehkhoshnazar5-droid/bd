from typing import Any
import secrets

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from app.core.confing import settings


router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


class AdminLoginRequest(BaseModel):
    password: str


async def _extract_login_payload(request: Request) -> dict[str, Any]:
    """Extract login payload from JSON or form submissions."""
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        json_payload = await request.json()
        return json_payload if isinstance(json_payload, dict) else {}

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        return {"password": form_data.get("password")}

    # Fallback: attempt form first (common browser case), then JSON
    try:
        form_data = await request.form()
        if form_data:
            return {"password": form_data.get("password")}
    except Exception:
        pass

    try:
        json_payload = await request.json()
        return json_payload if isinstance(json_payload, dict) else {}
    except Exception:
        return {}


@router.post("/login")
async def admin_login(request: Request):
    payload = await _extract_login_payload(request)

    try:
        data = AdminLoginRequest.parse_obj(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "فرمت درخواست ورود ادمین نامعتبر است",
                "errors": exc.errors(),
            },
        ) from exc

    if not secrets.compare_digest(data.password, settings.admin_login_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز عبور ادمین اشتباه است",
        )

    return {"detail": "ورود ادمین موفق بود"}