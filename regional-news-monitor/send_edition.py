"""Send a prepared edition after the workflow durably claims its date."""
from datetime import datetime
from email.message import EmailMessage
from email.utils import parseaddr
from os import environ
from pathlib import Path
import smtplib
import ssl
from zoneinfo import ZoneInfo

today = datetime.now(ZoneInfo("Europe/Nicosia")).date().isoformat()
edition = Path("public/archive") / today
sender = environ["NEWS_SMTP_USER"]
recipients = [parseaddr(value.strip())[1] for value in environ["NEWS_RECIPIENTS"].split(",") if value.strip()]
if not recipients or any("@" not in address for address in recipients):
    raise ValueError("Configure valid newsletter recipient addresses")
message = EmailMessage()
message["Subject"] = f"Regional News Monitor — {today}"
message["From"] = sender
message["To"] = sender
message.set_content(edition.with_suffix(".txt").read_text())
html = edition.with_suffix(".html").read_text()
message.add_alternative(html.split("<main>", 1)[1].split("</main>", 1)[0], subtype="html")
with smtplib.SMTP_SSL(environ.get("NEWS_SMTP_HOST") or "smtp.gmail.com",
                      int(environ.get("NEWS_SMTP_PORT") or 465),
                      context=ssl.create_default_context(), timeout=30) as smtp:
    smtp.login(sender, environ["NEWS_SMTP_PASSWORD"])
    refused = smtp.send_message(message, from_addr=sender, to_addrs=recipients)
    if refused:
        raise RuntimeError("The SMTP server refused one or more recipients")
