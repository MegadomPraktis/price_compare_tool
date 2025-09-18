import smtplib
from email.message import EmailMessage
from pathlib import Path

from ..config import settings


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        data = Path(attachment_path).read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=Path(attachment_path).name,
        )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        if settings.SMTP_USER and settings.SMTP_PASS:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
        s.send_message(msg)
