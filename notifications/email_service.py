"""
Email Service for sending notifications via SMTP.

Supports Gmail, Outlook, or any SMTP server.

# TODO: Configurar credenciales SMTP antes de enviar notificaciones
#       Para Gmail:
#       1. Habilitar "Acceso de apps menos seguras" o crear "App Password"
#       2. Ir a https://myaccount.google.com/apppasswords
#       3. Generar una contraseña de aplicación
#       4. Usar esa contraseña en SMTP_PASSWORD
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

# SMTP Configuration
# Default: Gmail SMTP (can be changed to Outlook, etc.)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Your email address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App password for Gmail
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "pedropablost@icloud.com")
DEFAULT_RECIPIENT = os.getenv("DEFAULT_RECIPIENT", "p.sanin@uniandes.edu.co")

# Email sending enabled flag (disable if no SMTP configured)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"


async def send_notification_email(
    recipient_email: str,
    subject: str,
    message: str,
    sender_username: str
) -> bool:
    """
    Send a notification email via SMTP.
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject
        message: Notification message
        sender_username: Username of who sent the notification
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if email is enabled
    if not EMAIL_ENABLED:
        print(f"📧 Email disabled. Would send to: {recipient_email}")
        print(f"   Subject: {subject}")
        print(f"   Message: {message}")
        return True  # Return True to not block the notification flow
    
    # Check SMTP credentials
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️  SMTP credentials not configured. Email not sent.")
        return False
    
    # Use default recipient for testing
    actual_recipient = recipient_email or DEFAULT_RECIPIENT
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ProvesiWMS] {subject}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = actual_recipient
        
        # Plain text version
        text_content = f"""
Nueva notificación de ProvesiWMS
================================

De: {sender_username}
Mensaje: {message}

---
Este es un mensaje automático del sistema de notificaciones de ProvesiWMS.
        """
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #2196F3; color: white; padding: 15px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
        .message {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">📬 Nueva Notificación</h2>
        </div>
        <p><strong>De:</strong> {sender_username}</p>
        <div class="message">
            <p>{message}</p>
        </div>
        <div class="footer">
            <p>Este es un mensaje automático del sistema de notificaciones de ProvesiWMS.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both versions
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Connect and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, actual_recipient, msg.as_string())
        
        print(f"✅ Email sent to {actual_recipient}!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {str(e)}")
        print("   Tip: For Gmail, use an App Password instead of your regular password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending email: {str(e)}")
        return False


async def send_bulk_notification_emails(
    recipients: List[str],
    subject: str,
    message: str,
    sender_username: str
) -> dict:
    """
    Send notification to multiple recipients.
    
    Returns:
        Dict with 'success' and 'failed' counts
    """
    results = {"success": 0, "failed": 0}
    
    for recipient in recipients:
        if await send_notification_email(recipient, subject, message, sender_username):
            results["success"] += 1
        else:
            results["failed"] += 1
    
    return results
