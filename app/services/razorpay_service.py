import razorpay
from app.config import settings
from datetime import datetime, timedelta

client = None

if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_payment_link(
    amount: int,
    description: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    reference_id: str,
    callback_url: str,
    notes: dict = None
):
    if not client:
        raise Exception("Razorpay client not initialized")
    
    expire_by = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    
    data = {
        "upi_link": True,
        "amount": amount * 100,
        "currency": "INR",
        "accept_partial": False,
        "expire_by": expire_by,
        "reference_id": reference_id,
        "description": description,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "contact": customer_phone
        },
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "notes": notes or {},
        "callback_url": callback_url,
        "callback_method": "get"
    }
    return client.payment_link.create(data=data)

def fetch_payment_link(payment_link_id: str):
    if not client:
        raise Exception("Razorpay client not initialized")
    return client.payment_link.fetch(payment_link_id)

def verify_payment_link_signature(payment_link_id: str, payment_link_reference_id: str, payment_link_status: str, razorpay_signature: str):
    if not client:
        raise Exception("Razorpay client not initialized")
    
    params_dict = {
        "payment_link_id": payment_link_id,
        "payment_link_reference_id": payment_link_reference_id,
        "payment_link_status": payment_link_status,
        "razorpay_signature": razorpay_signature
    }
    return client.utility.verify_payment_link_signature(params_dict)

def verify_webhook_signature(body: str, signature: str, secret: str):
    if not client:
        raise Exception("Razorpay client not initialized")
    return client.utility.verify_webhook_signature(body, signature, secret)