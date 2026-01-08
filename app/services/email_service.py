import aiosmtplib
from email.message import EmailMessage
from app.config import settings

async def send_email(subject: str, recipients: list[str], body: str):
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP settings not configured, skipping email.")
        return

    message = EmailMessage()
    message["From"] = settings.FROM_EMAIL
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True
        )
        print(f"Email sent to {recipients}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def send_event_registration_email(to_email: str, event_title: str, event_date: str):
    subject = f"Registration Confirmed - {event_title}"
    body = f"""
    Hello,

    Your registration for {event_title} has been confirmed.
    
    Date: {event_date}
    
    See you there!
    Team TALOS
    """
    await send_email(subject, [to_email], body)

async def send_workshop_payment_success_email(to_email: str, workshop_title: str, amount: int):
    subject = f"Payment Successful - {workshop_title}"
    body = f"""
    Hello,

    We have received your payment of INR {amount} for {workshop_title}.
    Your registration is confirmed.
    
    See you there!
    Team TALOS
    """
    await send_email(subject, [to_email], body)
