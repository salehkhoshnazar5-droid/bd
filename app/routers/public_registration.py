import re
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.confing import settings
from app.services.email_service import send_registration_confirmation_email

router = APIRouter(prefix="/public", tags=["Public Registration"])
templates = Jinja2Templates(directory="app/templates")

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,64}$")


def _is_https_request(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        return forwarded_proto.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"


@router.get("/register", response_class=HTMLResponse)
async def public_registration_page(request: Request, error_message: str | None = None):
    return templates.TemplateResponse(
        "public/register.html",
        {
            "request": request,
            "error_message": error_message,
            "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
            "terms_link": "/public/terms",
        },
    )


@router.post("/register", response_class=HTMLResponse)
async def submit_public_registration(
    request: Request,
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    accept_terms: str | None = Form(None),
):
    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) < 2:
        return templates.TemplateResponse(
            "public/register.html",
            {
                "request": request,
                "error_message": "Please enter a valid name.",
                "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
                "terms_link": "/public/terms",
            },
            status_code=400,
        )

    if not EMAIL_PATTERN.match(email):
        return templates.TemplateResponse(
            "public/register.html",
            {
                "request": request,
                "error_message": "Please provide a valid email address.",
                "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
                "terms_link": "/public/terms",
            },
            status_code=400,
        )

    if not PASSWORD_PATTERN.match(password):
        return templates.TemplateResponse(
            "public/register.html",
            {
                "request": request,
                "error_message": "Password must be 8+ chars with upper, lower, number, and symbol.",
                "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
                "terms_link": "/public/terms",
            },
            status_code=400,
        )

    if accept_terms != "on":
        return templates.TemplateResponse(
            "public/register.html",
            {
                "request": request,
                "error_message": "You must accept the Terms and Conditions.",
                "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
                "terms_link": "/public/terms",
            },
            status_code=400,
        )

    if not _is_https_request(request) and request.url.hostname not in {"localhost", "127.0.0.1"}:
        return templates.TemplateResponse(
            "public/register.html",
            {
                "request": request,
                "error_message": "For your privacy, registration must be submitted via HTTPS.",
                "public_link": f"{settings.public_base_url.rstrip('/')}/public/register",
                "terms_link": "/public/terms",
            },
            status_code=400,
        )

    background_tasks.add_task(send_registration_confirmation_email, email, full_name)
    query = urlencode({"name": full_name, "email": email})
    return RedirectResponse(
        url=f"/public/thank-you?{query}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/thank-you", response_class=HTMLResponse)
async def registration_thank_you_page(
    request: Request, name: str = "there", email: str = ""
):
    return templates.TemplateResponse(
        "public/thank_you.html",
        {"request": request, "name": name, "email": email},
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse("public/terms.html", {"request": request})