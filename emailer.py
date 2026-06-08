"""
emailer.py — Email the finished infographic PNG + writeup via Gmail SMTP.

Auth  : Gmail App Password (16-digit, not your account password).
Setup : Enable 2-FA on Google, then create an App Password at
        https://myaccount.google.com/apppasswords

Subject : 🖼️ Daily Infographic — {topic}
Body    : the writeup/caption, ready to copy-paste.
Attach  : infographic.png (as a downloadable file).
"""

import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def send_infographic_email(png_path: str, topic: str, caption: str,
                           content: dict | None = None) -> bool:
    """Send the infographic PNG + copy-ready writeup. Returns True on success."""
    if not config.GMAIL_APP_PASSWORD:
        logger.error("GMAIL_APP_PASSWORD is not set — cannot send email.")
        return False

    subject = f"🖼️ Daily Infographic — {topic}"
    body = _build_body(topic, caption, content or {})

    msg = MIMEMultipart()
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if png_path and os.path.exists(png_path):
        _attach_png(msg, png_path)
    else:
        logger.warning("PNG missing (%s) — sending text-only email.", png_path)

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.sendmail(config.GMAIL_USER, config.RECIPIENT_EMAIL, msg.as_string())
        logger.info("Email sent to %s — %s", config.RECIPIENT_EMAIL, subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail auth failed. Check GMAIL_APP_PASSWORD and 2-FA.")
    except smtplib.SMTPException as exc:
        logger.error("SMTP error: %s", exc)
    except OSError as exc:
        logger.error("Network error sending email: %s", exc)
    return False


def _build_body(topic: str, caption: str, content: dict) -> str:
    quote = content.get("quote_main", "")
    for t in ("<span class='n'>", "<span class='h'>", "</span>"):
        quote = quote.replace(t, "")

    line = "=" * 60
    parts = [
        f"Today's infographic:\n{topic}\n",
        line, "WRITEUP — COPY & PASTE", line,
        caption.strip(), "",
    ]
    if quote:
        parts += [line, "PINNED FACT", line, quote, ""]
    parts += [
        line,
        "Attached: infographic.png  (1800px, ready to post)",
        f"Brand: {config.BRAND_HANDLE} | {config.BRAND_X} | {config.BRAND_LINKEDIN}",
    ]
    return "\n".join(parts)


def _attach_png(msg: MIMEMultipart, png_path: str) -> None:
    """Attach as octet-stream so Gmail offers it as a download, not inline."""
    filename = os.path.basename(png_path)
    with open(png_path, "rb") as fh:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(fh.read())
    encoders.encode_base64(part)
    part.set_param("name", filename)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)
