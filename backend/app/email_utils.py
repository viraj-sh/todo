from email.message import EmailMessage
from fastapi.templating import Jinja2Templates
import aiosmtplib
from pathlib import Path

from app.config import settings

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


async def send_email(
    to_email: str, subject: str, text_content: str, html_content: str | None = None
):
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_content)
    if html_content:
        message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.mail_host,
        port=settings.mail_port,
        username=settings.mail_username,
        password=settings.mail_password.get_secret_value(),
        start_tls=settings.use_tls,
    )


async def send_forgot_password_email(to_email: str, username: str, reset_token: str):
    reset_url = f"{settings.frontend_url}/reset-password?reset_token={reset_token}"
    template = templates.env.get_template("password_reset.html")
    html_content = template.render(username=username, reset_url=reset_url)
    text_content = f"""Password Reset

Hi {username},

We received a request to reset your password. Use the link below to choose a new password.

Reset your password: {reset_url}

This reset link will expire in 1 hour.

If you did not request a password reset, you can safely ignore this email.

If the link does not work, copy and paste this URL into your browser:
{reset_url}

--
Automated email. Please do not reply.
"""
    await send_email(
        to_email,
        "Reset Your Password - Todo",
        text_content,
        html_content,
    )


async def send_password_reset_confirmation(to_email: str, username: str):
    template = templates.env.get_template("password_reset_confirmation.html")
    html_content = template.render(username=username)
    text_content = f"""Password Reset Successful

Hi {username},

Your password has been successfully reset.

If you made this change, no further action is required.

If you did not reset your password, please secure your account immediately and contact support.

--
Automated email. Please do not reply.
"""
    await send_email(
        to_email, "Password reset successful - Todo", text_content, html_content
    )


async def send_email_verification(to_email: str, username: str, token: str):
    verification_url = f"{settings.frontend_url}/api/user/verify?token={token}"
    template = templates.env.get_template("email_verification.html")
    html_content = template.render(username=username, verification_url=verification_url)
    text_content = f"""Email Verification

Hi {username},

Welcome!

Please verify your email address by clicking the link below:

Verify your email: {verification_url}

This verification link will expire in 24 hours.

If you did not create an account, you can safely ignore this email.

If the link does not work, copy and paste this URL into your browser:
{verification_url}

--
Automated email. Please do not reply.
"""
    await send_email(
        to_email, "Please verify your email address - Todo", text_content, html_content
    )


async def send_email_verification_confirmation(to_email: str, username: str):
    template = templates.env.get_template("email_verification_confirmation.html")
    html_content = template.render(username=username)
    text_content = f"""Email Verified Successfully

Hi {username},

Your email address has been successfully verified.

You can now access all features of your account.

If you did not verify this email, please contact support immediately.

--
Automated email. Please do not reply.
"""
    await send_email(
        to_email,
        subject="Email verified successfully - Todo",
        text_content=text_content,
        html_content=html_content,
    )
