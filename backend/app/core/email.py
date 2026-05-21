import smtplib
from email.message import EmailMessage
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(email_to: str, subject: str, html_content: str) -> None:
    """
    Sends an email using the SMTP configuration defined in settings.
    Throws exceptions on failure.
    """
    if not settings.SMTP_HOST:
        raise ValueError("SMTP_HOST is not configured in environment variables.")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = settings.EMAILS_FROM_EMAIL
    msg['To'] = email_to
    msg.set_content(html_content, subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Error sending email to {email_to}: {e}")
        raise
