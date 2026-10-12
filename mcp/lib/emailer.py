"""SMTP delivery for emails to Rahul.

Copied from send_email in chat/rag/service.py: chat/ and mcp/ are separate Vercel
projects and can't import from each other. Keep the two in sync.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(subject: str, text_body: str) -> None:
    email_address = os.getenv("EMAIL_ADDRESS")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    if not all((email_address, smtp_server, app_password)):
        raise RuntimeError(
            "EMAIL_ADDRESS, EMAIL_SMTP_SERVER and EMAIL_APP_PASSWORD are required."
        )

    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = email_address
    msg["Subject"] = subject
    msg.set_content(text_body)

    with smtplib.SMTP(smtp_server, 587, timeout=20) as server:
        server.starttls()
        server.login(email_address, app_password)
        server.send_message(msg)
