import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

EMAIL_SEND_FROM = "rafaelcgama@hotmail.com"
EMAIL_SEND_FROM_PASSWORD = ""
EMAIL_SEND_TO = "rafaelcgama@gmail.com"


def create_email_msg():
    server = smtplib.SMTP(host='smtp.office365.com', port=587) # Research authentication
    server.starttls()

    server.login(EMAIL_SEND_FROM, EMAIL_SEND_FROM_PASSWORD)

    msg = MIMEMultipart()  # create a message object

    # Setup the parameters of the message
    msg.update({
        'From': EMAIL_SEND_FROM,
        'To': EMAIL_SEND_TO,
        'Subject': f'Data Report {datetime.now().strftime("%Y/%d/%m")}'
    })

    # Attach the body with the msg instance
    body = "Please find the attached zip file with the latest data."
    msg.attach(body)

    # Specify the path to your zip file
    filename = "/Users/rafaelcgama/Projects/hotels/data/data.zip"

    # Open the zip file in binary mode
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
    send_email(create_email_msg()[0])
