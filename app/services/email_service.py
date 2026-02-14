import logging
import smtplib
from email.message import EmailMessage

from app.core.confing import settings

logger = logging.getLogger(__name__)


def send_registration_confirmation_email(to_email: str, full_name: str) -> None:
    """Send a registration confirmation email using configured SMTP settings."""
    if not settings.smtp_host:
        logger.info(
            "SMTP is not configured. Skipping confirmation email for %s", to_email
        )
        return

    message = EmailMessage()
    message["Subject"] = "Registration successful"
    message["From"] = settings.email_from
    message["To"] = to_email
    message.set_content(
        (
            f"Hello {full_name},\n\n"
            "Thank you for registering. Your account request was received successfully.\n"
            "If you did not submit this request, please ignore this email.\n\n"
            "Regards,\nSupport Team"
        )
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send registration confirmation email to %s", to_email)