import os
import sys
sys.path.append('app')

from app.utils.mail_sender import send_invitation_email, send_welcome_email

def main():
    # Configurar credenciales si no están en variables de entorno
    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASSWORD"):
        smtp_user = input("Ingresa tu email de Zoho: ")
        smtp_password = input("Ingresa tu contraseña de aplicación de Zoho: ")
        os.environ["SMTP_USER"] = smtp_user
        os.environ["SMTP_PASSWORD"] = smtp_password
        os.environ["SMTP_SERVER"] = "smtp.zoho.com"
        os.environ["SMTP_PORT"] = "587"

    # Lista de emails a invitar (puedes modificar esto para leer de un archivo)
    emails_to_invite = [
        "invitado1@example.com",
        "invitado2@example.com",
        # Agrega más emails aquí
    ]

    inviter_name = "El equipo de Esquel ahorra"  # Puedes cambiar esto

    for email in emails_to_invite:
        send_invitation_email(email, inviter_name)
        # Si también quieres enviar bienvenida, descomenta la línea siguiente
        # send_welcome_email(email, "Usuario")  # Necesitas el username

if __name__ == "__main__":
    main()