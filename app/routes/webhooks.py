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
    if event == "payment.captured" or event == "order.paid":
        payment_ref = db.collection("payments").document(order_id)
        doc = payment_ref.get()
        if doc.exists:
            payment_data = doc.to_dict()
            payment_ref.update({
                "status": "captured",
                "payment_id": payment_entity.get("id"),
                "updated_at": datetime.utcnow()
            })
            
            # Create registration if not exists (recovery for closed window)
            workshop_id = payment_data.get("workshop_id")
            if workshop_id and not payment_data.get("registration_id"):
                import uuid
                from app.services.email_service import send_workshop_payment_success_email
                
                reg_id = str(uuid.uuid4())
                workshop_doc = db.collection("workshops").document(workshop_id).get()
                workshop_data = workshop_doc.to_dict() if workshop_doc.exists else {}
                
                reg_data = {
                    "registration_id": reg_id,
                    "workshop_id": workshop_id,
                    "workshop_name": workshop_data.get("title", ""),
                    "name": payment_data.get("name"),
                    "email": payment_data.get("email"),
                    "phone": payment_data.get("phone"),
                    "year": payment_data.get("year"),
                    "college_name": payment_data.get("college_name"),
                    "referral_id": payment_data.get("referral_id"),
                    "payment_id": payment_entity.get("id"),
                    "order_id": order_id,
                    "amount": payment_data.get("amount"),
                    "payment_status": "completed",
                    "status": "confirmed",
                    "registered_at": datetime.utcnow(),
                    "payment_completed_at": datetime.utcnow()
                }
                
                db.collection(f"{workshop_id}_registrations").document(reg_id).set(reg_data)
                payment_ref.update({"registration_id": reg_id})
                
                background_tasks.add_task(
                    send_workshop_payment_success_email,
                    payment_data.get("email"),
                    workshop_data.get("title"),
                    payment_data.get("amount", 0)
                )
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
