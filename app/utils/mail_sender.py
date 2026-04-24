import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_welcome_email(to_email: str, username: str, referral_code: str = None):
    # Configuración básica, ajustar con variables de entorno
    smtp_server = os.getenv("SMTP_SERVER", "smtp.zoho.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    frontend_url = os.getenv("FRONTEND_URL", "https://esquel-ahorra.online")

    if not smtp_user or not smtp_password:
        print(f"Email de bienvenida a {to_email}: Bienvenido {username} a Esquel ahorra!")
        return

    # Crear mensaje multipart para HTML
    msg = MIMEMultipart("alternative")
    msg['Subject'] = "¡Bienvenido a Esquel ahorra!"
    msg['From'] = f"Esquel Ahorra <{smtp_user}>"
    msg['To'] = to_email

    # Generar link de invitación
    invite_link = f"{frontend_url}/register?ref={referral_code}" if referral_code else None
    
    referral_section = ""
    if invite_link:
        referral_section = f"""
        <div style="background-color: #f0f7ff; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #cce3ff;">
            <h3 style="color: #0056b3; margin-top: 0;">¡Invita a tus amigos y gana puntos!</h3>
            <p>Comparte tu enlace único de invitación y obtén 50 puntos por cada persona que se registre:</p>
            <p style="word-break: break-all;"><strong><a href="{invite_link}">{invite_link}</a></strong></p>
            <p>Tu código de referido es: <strong>{referral_code}</strong></p>
        </div>
        """

    # Contenido HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">¡Bienvenido a Esquel ahorra, {username}!</h2>
            <p>Gracias por registrarte en nuestra plataforma. Estamos emocionados de tenerte con nosotros.</p>
            <p>En Esquel ahorra, encontrarás las mejores ofertas y precios en productos en locales de la zona.</p>
            
            {referral_section}

            <p>¡Empieza a explorar y ahorra hoy mismo!</p>
            <br>
            <p>Saludos,<br>El equipo de Esquel ahorra</p>
        </div>
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

def send_invitation_email(to_email: str, inviter_name: str = "El equipo"):
    # Configuración básica, ajustar con variables de entorno
    smtp_server = os.getenv("SMTP_SERVER", "smtp.zoho.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print(f"Email de invitación a {to_email}: ¡Únete a Esquel ahorra!")
        return

    # Crear mensaje multipart para HTML
    msg = MIMEMultipart("alternative")
    msg['Subject'] = "¡Te invitamos a unirte a Esquel ahorra!"
    msg['From'] = smtp_user
    msg['To'] = to_email

    # Contenido HTML
    html = f"""
    <html>
    <body>
        <h2>¡Hola!</h2>
        <p>{inviter_name} te invita a unirte a Esquel ahorra, la plataforma donde encuentras las mejores ofertas y precios en productos locales.</p>
        <p>Regístrate hoy y comienza a ahorrar en tus compras diarias.</p>
        <p>¡No esperes más, únete a la comunidad!</p>
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
        print(f"Email de invitación enviado exitosamente a {to_email}")
    except Exception as e:
        print(f"Error enviando email: {e}")
