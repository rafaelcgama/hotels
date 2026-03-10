import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from src.config import EMAIL_SEND_FROM, EMAIL_SEND_FROM_PASSWORD, EMAIL_SEND_TO, DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

def login_smtp(username, password):
    """Authenticate and return SMTP connection based on domain."""
    domain = username.partition('@')[2].rsplit('.', 2)[0]
    domain_map = {
        'hotmail': 'smtp.office365.com',
        'outlook': 'smtp.office365.com',
        'gmail': 'smtp.gmail.com'
    }
    
    server_host = domain_map.get(domain, 'smtp.gmail.com') # fallback to gmail
    
    try:
        server = smtplib.SMTP(host=server_host, port=587)
        server.starttls()
        server.login(username, password)
        return server
    except Exception as e:
        logger.error(f"Failed to connect and login to SMTP server {server_host}: {e}")
        return None

def send_notification_email():
    """Compiles the email with the SQLite DB attached and sends it."""
    if not EMAIL_SEND_FROM or not EMAIL_SEND_FROM_PASSWORD or not EMAIL_SEND_TO:
        logger.error("Email credentials are not fully configured in .env. Skipping email notification.")
        return

    logger.info("Preparing email notification...")
    server = login_smtp(EMAIL_SEND_FROM, EMAIL_SEND_FROM_PASSWORD)
    if not server:
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SEND_FROM
    msg['To'] = EMAIL_SEND_TO
    msg['Subject'] = f'Hotel Price Data Report - {datetime.now().strftime("%Y-%m-%d")}'

    body = "Please find the attached SQLite database file containing the latest hotel price data."
    msg.attach(MIMEText(body, "plain"))

    # Attach the DB file
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=prices_{datetime.now().strftime('%Y%m%d')}.db"
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Error reading or attaching DB file {DB_PATH}: {e}")
    else:
        logger.warning(f"Database attachment not found at {DB_PATH}. Sending email without attachment.")
        body_update = "\n\n[WARNING] The database file was not found and is missing from this report."
        msg.attach(MIMEText(body_update, "plain"))

    try:
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        logger.info("Notification email sent successfully!")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
    finally:
        server.quit()
