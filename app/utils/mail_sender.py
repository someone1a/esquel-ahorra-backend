import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_welcome_email(to_email: str, username: str):
    # Configuración básica, ajustar con variables de entorno
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print(f"Email de bienvenida a {to_email}: Bienvenido {username} a Esquel ahorra!")
        return

    # Crear mensaje multipart para HTML
    msg = MIMEMultipart("alternative")
    msg['Subject'] = "¡Bienvenido a Esquel ahorra!"
    msg['From'] = smtp_user
    msg['To'] = to_email

    # Contenido HTML
    html = f"""
    <html>
    <body>
        <h2>¡Bienvenido a Esquel ahorra, {username}!</h2>
        <p>Gracias por registrarte en nuestra plataforma. Estamos emocionados de tenerte con nosotros.</p>
        <p>En Esquel ahorra, encontrarás las mejores ofertas y precios en productos locales.</p>
        <p>¡Empieza a explorar y ahorra hoy mismo!</p>
        <br>
        <p>Saludos,<br>El equipo de Esquel ahorra</p>
    </body>
    </html>
    """

    # Adjuntar HTML
    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"Email de bienvenida enviado exitosamente a {to_email}")
    except Exception as e:
        print(f"Error enviando email: {e}")