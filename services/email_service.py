import smtplib
import ssl
import logging
from email.message import EmailMessage
from config import Config

logger = logging.getLogger(__name__)

SMTP_PROVIDERS = {
    "gmail.com":      {"host": "smtp.gmail.com",      "port": 587},
    "yahoo.com":      {"host": "smtp.mail.yahoo.com", "port": 587},
    "yahoo.in":       {"host": "smtp.mail.yahoo.com", "port": 587},
    "outlook.com":    {"host": "smtp.office365.com",  "port": 587},
    "hotmail.com":    {"host": "smtp.office365.com",  "port": 587},
    "live.com":       {"host": "smtp.office365.com",  "port": 587},
    "icloud.com":     {"host": "smtp.mail.me.com",    "port": 587},
    "zoho.com":       {"host": "smtp.zoho.com",       "port": 587},
    "protonmail.com": {"host": "smtp.protonmail.com", "port": 587},
}

def get_smtp_settings(email: str) -> dict:
    """
    Retrieves the SMTP host and port settings based on the email domain.
    """
    if not email or "@" not in email:
        return {"host": "smtp.gmail.com", "port": 587} # fallback
        
    domain = email.split("@")[-1].lower()
    if domain in SMTP_PROVIDERS:
        return SMTP_PROVIDERS[domain]
        
    return {"host": f"smtp.{domain}", "port": 587}

def send_mashup_email(recipient_email: str, artist_name: str, num_songs: int, duration: int, attachment_path: str, progress_callback=None) -> None:
    """
    Sends the zip archive containing the mashup to the recipient email.
    """
    if progress_callback:
        progress_callback("Connecting to SMTP server and sending email...")

    sender_email = Config.SENDER_EMAIL
    sender_password = Config.SENDER_APP_PASSWORD
    
    if not sender_email or not sender_password:
        raise Exception("SENDER_EMAIL or SENDER_APP_PASSWORD is not configured on the server.")

    smtp_settings = get_smtp_settings(sender_email)
    logger.info(f"Connecting to SMTP: {smtp_settings['host']}:{smtp_settings['port']} using {sender_email}")

    # Build the email message
    msg = EmailMessage()
    msg["Subject"] = f"Your {artist_name} Mashup is Ready!"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    
    body = (
        f"Hello,\n\n"
        f"Your custom YouTube audio mashup is ready!\n\n"
        f"Details:\n"
        f"- Artist: {artist_name}\n"
        f"- Number of Songs: {num_songs}\n"
        f"- Slices Duration: {duration} seconds each\n\n"
        f"Find your mashup.mp3 file inside the attached ZIP archive.\n\n"
        f"Enjoy,\n"
        f"YouTube Mashup Creator Service"
    )
    msg.set_content(body)

    # Attach the zip file
    try:
        with open(attachment_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="zip",
                filename=f"{artist_name.replace(' ', '_')}_mashup.zip"
            )
    except Exception as e:
        logger.error(f"Failed to read attachment file: {str(e)}")
        raise Exception(f"Failed to attach file: {str(e)}")

    # Connect and send securely
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_settings["host"], smtp_settings["port"], timeout=30) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logger.info(f"Email successfully sent to {recipient_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        raise Exception("Email login failed. Please verify that SENDER_APP_PASSWORD is correct and allows App access.")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise Exception(f"SMTP error: {str(e)}")
