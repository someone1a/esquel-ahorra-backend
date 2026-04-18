import smtplib
from email.mime.text import MIMEText
import os

def send_welcome_email(to_email: str, username: str):
    # Configuración básica, ajustar con variables de entorno
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print(f"Email de bienvenida a {to_email}: Bienvenido {username}!")
        return

    msg = MIMEText(f"Bienvenido {username} a EsquelAhorra!")
    msg['Subject'] = "Bienvenido"
    msg['From'] = smtp_user
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error enviando email: {e}")