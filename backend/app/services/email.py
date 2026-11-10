import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Send an email via SMTP. Returns True on success, False on failure."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("SMTP not configured — email not sent to %s", to_email)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, type(e).__name__)
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    """Send an email verification link."""
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    subject = "Verify your Real-Life Rivals account"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Welcome to Real-Life Rivals!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_url}" style="background: #10b981; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Verify Email</a></p>
        <p>Or copy this link: {verify_url}</p>
        <p>This link expires in 24 hours.</p>
        <p>If you didn't create an account, you can ignore this email.</p>
    </div>
    """
    text_body = f"Verify your Real-Life Rivals account: {verify_url}\n\nThis link expires in 24 hours."
    return send_email(to_email, subject, html_body, text_body)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Send a password reset link."""
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    subject = "Reset your Real-Life Rivals password"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}" style="background: #10b981; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Reset Password</a></p>
        <p>Or copy this link: {reset_url}</p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request a password reset, you can ignore this email.</p>
    </div>
    """
    text_body = f"Reset your Real-Life Rivals password: {reset_url}\n\nThis link expires in 1 hour."
    return send_email(to_email, subject, html_body, text_body)
