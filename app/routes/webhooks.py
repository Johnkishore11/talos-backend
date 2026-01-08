from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from app.services import razorpay_service
from app.services.firebase_service import db
from app.config import settings
from datetime import datetime
import json

router = APIRouter()

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_razorpay_signature: str = Header(None)
):
    if not settings.RAZORPAY_WEBHOOK_SECRET:
         # Log warning or skip validation if secret not set (dev mode)
         pass

    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')

    # 1. Verify Signature
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        try:
            razorpay_service.verify_webhook_signature(body_str, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET)
        except Exception:
             raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # 2. Parse Event
    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = data.get("event")
    payload = data.get("payload", {})
    payment_entity = payload.get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    
    if not order_id:
        return {"status": "ignored", "reason": "no_order_id"}

    # 3. Handle Events
    if event == "payment.captured":
        # Update payment status
        payment_ref = db.collection("payments").document(order_id)
        doc = payment_ref.get()
        if doc.exists:
            payment_ref.update({
                "status": "captured",
                "payment_id": payment_entity.get("id"),
                "updated_at": datetime.utcnow()
            })
            
            # Logic to create registration if not exists could go here
            # But usually verify-payment handles it. 
            # If verify-payment failed or user closed window, we might need to recover here.
        else:
            print(f"Payment record for order {order_id} not found in webhook")

    elif event == "payment.failed":
        payment_ref = db.collection("payments").document(order_id)
        if payment_ref.get().exists:
             payment_ref.update({
                "status": "failed",
                "updated_at": datetime.utcnow()
            })

    return {"status": "ok"}
