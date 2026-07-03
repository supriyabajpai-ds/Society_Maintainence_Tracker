"""Email notifications.

Works with any free SMTP service (Brevo, Gmail app password, Mailtrap...).
If SMTP is not configured via env vars, emails are printed to the console
so the app remains fully testable in development.
"""

import os
import smtplib
from email.mime.text import MIMEText


def _smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def send_email(to: str, subject: str, body: str) -> None:
    if not _smtp_configured():
        print(f"\n[EMAIL - console fallback]\nTo: {to}\nSubject: {subject}\n{body}\n")
        return

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM", username)

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.sendmail(sender, [to], msg.as_string())
    except Exception as exc:  # never let email failures break the API
        print(f"[EMAIL ERROR] {exc}")


def notify_status_change(to: str, resident_name: str, complaint_title: str,
                         new_status: str, note: str | None) -> None:
    body = (
        f"Hi {resident_name},\n\n"
        f"Your complaint \"{complaint_title}\" has been updated.\n"
        f"New status: {new_status}\n"
    )
    if note:
        body += f"Note from admin: {note}\n"
    body += "\nYou can view the full history by logging in to Nivaas.\n\n— Nivaas Society Desk"
    send_email(to, f"Complaint update: {new_status} — {complaint_title}", body)


def notify_important_notice(to: str, resident_name: str, title: str, notice_body: str) -> None:
    body = (
        f"Hi {resident_name},\n\n"
        f"An important notice has been posted on the society notice board:\n\n"
        f"{title}\n{'-' * len(title)}\n{notice_body}\n\n— Nivaas Society Desk"
    )
    send_email(to, f"Important notice: {title}", body)
