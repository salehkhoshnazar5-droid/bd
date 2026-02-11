from typing import Optional

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.admin_auth_service import (
    authenticate_admin_password,
    create_admin_token,
    is_admin_authenticated,
)

router = APIRouter(prefix="/ui-auth/admin", tags=["Admin UI Authentication"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error_message: Optional[str] = None):
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "title": "ورود مدیر سیستم",
            "error_message": error_message,
            "redirect_url": request.query_params.get("redirect", "/admin/dashboard"),
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def admin_login_submit(
    request: Request,
    password: str = Form(...),
    redirect_url: Optional[str] = Form("/admin/dashboard"),
):
    authenticated, error_message = authenticate_admin_password(request, password)
    if not authenticated:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "title": "ورود مدیر سیستم",
                "error_message": error_message,
                "redirect_url": redirect_url,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="admin_access_token",
        value=create_admin_token(),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
    )
    return response


@router.get("/logout")
async def admin_logout():
    response = RedirectResponse(url="/ui-auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_access_token")
    return response