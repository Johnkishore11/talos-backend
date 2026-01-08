from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.dependencies import get_current_user
from app.services.firebase_service import db
from app.services import razorpay_service
from app.services.email_service import send_workshop_payment_success_email
from app.models.workshop import Workshop, WorkshopRegistrationRequest, PaymentVerificationRequest
from app.config import settings
import uuid
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("", response_model=List[Workshop])
@router.get("/", response_model=List[Workshop])
async def get_workshops(status: Optional[str] = "open"):
    print(f"DEBUG: get_workshops called with status={status}")
    if status and status != "all":
        docs = db.collection("workshops").where("status", "==", status).stream()
    else:
        docs = db.collection("workshops").stream()
    
    results = [doc.to_dict() for doc in docs]
    print(f"DEBUG: found {len(results)} workshops")
    return results

@router.get("/{workshop_id}", response_model=Workshop)
async def get_workshop(workshop_id: str):
    doc = db.collection("workshops").document(workshop_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return doc.to_dict()


@router.post("/{workshop_id}/create-order")
async def create_workshop_order(
    workshop_id: str,
    registration: WorkshopRegistrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Razorpay order for workshop registration.
    Solo registration with payment.
    """
    
    # 1. Get Workshop Details
    workshop_ref = db.collection("workshops").document(workshop_id)
    workshop = workshop_ref.get()
    if not workshop.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    workshop_data = workshop.to_dict()
    
    # 2. Check if workshop is open (default to "open" if not set)
    workshop_status = workshop_data.get("status", "open") or "open"
    if workshop_status != "open":
        raise HTTPException(status_code=400, detail="Workshop registration is closed")
    
    amount = workshop_data.get("registration_fee", 0)
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="This workshop is free, use direct registration")

    # 3. Check if already registered (by email)
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", registration.email).where("status", "==", "confirmed").limit(1).get()
        
    if list(existing_reg):
        raise HTTPException(status_code=400, detail="This email is already registered for this workshop")

    # 4. Create Razorpay Order
    try:
        receipt = f"rcpt_{workshop_id[:8]}_{int(datetime.utcnow().timestamp())}"
        notes = {
            "workshop_id": workshop_id,
            "email": registration.email,
            "name": registration.name
        }
        order = razorpay_service.create_order(amount, currency="INR", receipt=receipt, notes=notes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment initialization failed: {str(e)}")

    # 5. Save pending payment info
    payment_doc_id = order["id"]
    payment_data = {
        "payment_id": payment_doc_id,
        "order_id": order["id"],
        "workshop_id": workshop_id,
        "email": registration.email,
        "name": registration.name,
        "phone": registration.phone,
        "year": registration.year,
        "college_name": registration.college_name,
        "referral_id": registration.referral_id,
        "amount": amount,
        "currency": "INR",
        "status": "created",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.collection("payments").document(payment_doc_id).set(payment_data)

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": settings.RAZORPAY_KEY_ID
    }


@router.post("/{workshop_id}/verify-payment")
async def verify_workshop_payment(
    workshop_id: str,
    verification: PaymentVerificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify Razorpay payment and complete workshop registration.
    Stores registration in {workshop_id}_registrations collection.
    """
    
    # 1. Verify Signature
    params_dict = {
        "razorpay_order_id": verification.razorpay_order_id,
        "razorpay_payment_id": verification.razorpay_payment_id,
        "razorpay_signature": verification.razorpay_signature
    }
    
    try:
        razorpay_service.verify_payment_signature(params_dict)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # 2. Get Workshop Details
    workshop_doc = db.collection("workshops").document(workshop_id).get()
    if not workshop_doc.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    workshop_data = workshop_doc.to_dict()

    # 3. Create Registration in workshop-specific collection
    reg_id = str(uuid.uuid4())
    reg_data = {
        "registration_id": reg_id,
        "workshop_id": workshop_id,
        "workshop_name": workshop_data.get("title", ""),
        
        # Participant Info
        "name": verification.name,
        "email": verification.email,
        "phone": verification.phone,
        "year": verification.year,
        "college_name": verification.college_name,
        "referral_id": verification.referral_id,
        
        # Payment Info
        "payment_id": verification.razorpay_payment_id,
        "order_id": verification.razorpay_order_id,
        "amount": workshop_data.get("registration_fee", 0),
        "payment_status": "completed",
        
        # Metadata
        "status": "confirmed",
        "registered_at": datetime.utcnow(),
        "payment_completed_at": datetime.utcnow()
    }
    
    # Store in workshop-specific collection
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    registrations_ref.document(reg_id).set(reg_data)
    
    # 4. Update Payment Record
    payment_ref = db.collection("payments").document(verification.razorpay_order_id)
    if payment_ref.get().exists:
        payment_ref.update({
            "status": "captured",
            "registration_id": reg_id,
            "razorpay_signature": verification.razorpay_signature,
            "updated_at": datetime.utcnow()
        })

    # 5. Send confirmation email
    if verification.email:
        background_tasks.add_task(
            send_workshop_payment_success_email,
            verification.email,
            workshop_data.get("title"),
            workshop_data.get("registration_fee", 0)
        )

    return {"message": "Registration confirmed", "registration_id": reg_id}


@router.get("/{workshop_id}/check-email")
async def check_email_registered(workshop_id: str, email: str):
    """Check if an email is already registered for a workshop"""
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", email).where("status", "==", "confirmed").limit(1).get()
    
    return {"registered": bool(list(existing_reg))}


@router.get("/{workshop_id}/registrations")
async def get_workshop_registrations(
    workshop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all registrations for a workshop (admin use)"""
    # Check if workshop exists
    workshop_ref = db.collection("workshops").document(workshop_id)
    if not workshop_ref.get().exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    docs = registrations_ref.stream()
    
    return [doc.to_dict() for doc in docs]
