"""
Amazon SES Email Service for sending notifications.

# TODO: Verificar email pedropablost@icloud.com en Amazon SES antes de enviar notificaciones
#       1. Ir a AWS Console > SES > Verified identities
#       2. Click "Create identity" > Email address
#       3. Ingresar: pedropablost@icloud.com
#       4. Verificar el email haciendo click en el link enviado
"""
import os
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "pedropablost@icloud.com")
DEFAULT_RECIPIENT = os.getenv("DEFAULT_RECIPIENT", "p.sanin@uniandes.edu.co")

# SES Client (will use IAM role credentials on EC2)
ses_client = None


def get_ses_client():
    """Get or create SES client."""
    global ses_client
    if ses_client is None:
        ses_client = boto3.client('ses', region_name=AWS_REGION)
    return ses_client


async def send_notification_email(
    recipient_email: str,
    subject: str,
    message: str,
    sender_username: str
) -> bool:
    """
    Send a notification email via Amazon SES.
    
    Args:
        recipient_email: Email address to send to (defaults to p.sanin@uniandes.edu.co)
        subject: Email subject
        message: Notification message
        sender_username: Username of who sent the notification
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use default recipient for testing
    actual_recipient = recipient_email or DEFAULT_RECIPIENT
    
    try:
        client = get_ses_client()
        
        response = client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [actual_recipient]
            },
            Message={
                'Subject': {
                    'Data': f"[ProvesiWMS] {subject}",
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"""
Nueva notificación de ProvesiWMS
================================

De: {sender_username}
Mensaje: {message}

---
Este es un mensaje automático del sistema de notificaciones de ProvesiWMS.
                        """,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': f"""
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
                        """,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"✅ Email sent! Message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Failed to send email: {error_code} - {error_message}")
        
        # Common errors:
        # - MessageRejected: Email address not verified (sandbox mode)
        # - InvalidParameterValue: Invalid email format
        # - Throttling: Too many requests
        
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
