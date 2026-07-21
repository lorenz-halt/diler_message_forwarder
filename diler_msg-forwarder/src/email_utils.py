import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email_with_attachments(smtp_server, smtp_port, 
                                email_address, email_password, 
                                to_address, 
                                subject, body, attachments):
    msg = MIMEMultipart()
    msg['From'] = email_address
    # Accept comma-separated string or list for to_address
    if isinstance(to_address, list):
        msg['To'] = ', '.join(to_address)
    elif isinstance(to_address, str):
        msg['To'] = to_address
    else:
        msg['To'] = str(to_address)
    msg['Subject'] = subject
    # Use HTML encoding for better email appearance
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    for attachment_path in attachments:
        filename = os.path.basename(attachment_path)
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)