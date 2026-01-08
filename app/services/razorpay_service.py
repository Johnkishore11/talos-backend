import razorpay
from app.config import settings

client = None

if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_order(amount: int, currency: str = "INR", receipt: str = None, notes: dict = None):
    if not client:
        raise Exception("Razorpay client not initialized")
    
    data = {
        "amount": amount * 100, # Amount in paise
        "currency": currency,
        "receipt": receipt,
        "notes": notes
    }
    return client.order.create(data=data)

def verify_payment_signature(params_dict):
    if not client:
        raise Exception("Razorpay client not initialized")
    
    # params_dict should contain razorpay_order_id, razorpay_payment_id, razorpay_signature
    return client.utility.verify_payment_signature(params_dict)

def verify_webhook_signature(body: str, signature: str, secret: str):
    if not client:
        raise Exception("Razorpay client not initialized")
    return client.utility.verify_webhook_signature(body, signature, secret)
