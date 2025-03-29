import os
import smtplib
from email import encoders
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

EMAIL_SEND_FROM = "rafaelcgama@hotmail.com"
EMAIL_SEND_FROM_PASSWORD = ""
EMAIL_SEND_TO = "rafaelcgama@gmail.com"


def login(username, password):
    # Extract domain and map to SMTP host.
    domain = username.partition('@')[2].rsplit('.', 2)[0]
    domain_map = {
        'hotmail': 'smtp.office365.com',
        'outlook': 'smtp.office365.com',
        'gmail': 'smtp.gmail.com'
    }
    # Authenticate and return SMTP connection.
    server = smtplib.SMTP(host=domain_map[domain], port=587)  # Research authentication
    server.starttls()

    server.login(username, password)

    return server


def create_email_msg():
    server = login(EMAIL_SEND_FROM, EMAIL_SEND_FROM_PASSWORD)

    # Setup the parameters of the message
    msg = MIMEMultipart()  # create a message object
    msg['From'] = EMAIL_SEND_FROM
    msg['To'] = EMAIL_SEND_TO
    msg['Subject'] = f'Data Report {datetime.now().strftime("%Y/%d/%m")}'

    # Attach the body with the msg instance
    body = "Please find the attached zip file with the latest data."
    msg.attach(body)

    # Specify the path to your zip file
    filename = "/data/rates.zip"

    # Open the zip file in binary mode
    if os.path.exists(filename):
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode the attachment in base64
        encoders.encode_base64(part)

        # Add header with file name
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filename.split('/')[-1]}",  # Extracts the file name from the path
        )

        # Attach the part (zip file) to the message
        msg.attach(part)
    else:
        print(f"[WARNING] Attachment not found: {filename}")

    return server, msg


def send_email(server, msg):
    # Send the email
    try:
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

    # Quit the SMTP session
    server.quit()


if __name__ == '__main__':
    server, msg = create_email_msg()
    send_email(server, msg)
