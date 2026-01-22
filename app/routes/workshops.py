from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.dependencies import get_current_user, get_optional_user
from app.services.firebase_service import db
from app.services import razorpay_service
from app.services.email_service import send_workshop_payment_success_email
from app.services.google_sheets_service import get_google_sheets_service
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


@router.post("/{workshop_id}/create-payment-link")
async def create_workshop_payment_link(
    workshop_id: str,
    registration: WorkshopRegistrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Razorpay payment link for workshop registration.
    Returns payment link URL for user to complete payment.
    """
    
    # 1. Get Workshop Details
    workshop_ref = db.collection("workshops").document(workshop_id)
    workshop = workshop_ref.get()
    if not workshop.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    workshop_data = workshop.to_dict()
    
    # 2. Check if workshop is open
    workshop_status = workshop_data.get("status", "open") or "open"
    if workshop_status != "open":
        raise HTTPException(status_code=400, detail="Workshop registration is closed")
    
    amount = workshop_data.get("registration_fee", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="This workshop is free, use direct registration")

    # 3. Check if already registered
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", registration.email).limit(1).get()
    if list(existing_reg):
        raise HTTPException(status_code=400, detail="This email is already registered for this workshop")

    # 4. Create Payment Link
    try:
        reference_id = f"{workshop_id}_{int(datetime.utcnow().timestamp())}"
        callback_url = f"{settings.FRONTEND_URL}/workshops/{workshop_id}/payment-success"
        
        payment_link = razorpay_service.create_payment_link(
            amount=amount,
            description=f"Registration for {workshop_data.get('title', 'Workshop')}",
            customer_name=registration.name,
            customer_email=registration.email,
            customer_phone=registration.phone,
            reference_id=reference_id,
            callback_url=callback_url,
            notes={
                "workshop_id": workshop_id,
                "email": registration.email,
                "name": registration.name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment link creation failed: {str(e)}")

    # 5. Save pending payment info
    payment_doc_id = payment_link["id"]
    payment_data = {
        "payment_link_id": payment_link["id"],
        "reference_id": reference_id,
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
        "short_url": payment_link["short_url"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.collection("payments").document(payment_doc_id).set(payment_data)

    return {
        "payment_link_id": payment_link["id"],
        "short_url": payment_link["short_url"],
        "amount": amount,
        "reference_id": reference_id
    }


@router.get("/{workshop_id}/payment-callback")
async def payment_callback(
    workshop_id: str,
    payment_link_id: str,
    payment_link_reference_id: str,
    payment_link_status: str,
    background_tasks: BackgroundTasks,
    razorpay_payment_id: str = None,
    razorpay_signature: str = None
):
    """
    Handle payment link callback from Razorpay.
    Verifies signature and creates registration.
    """
    
    # 1. Verify Signature
    if razorpay_signature:
        try:
            razorpay_service.verify_payment_link_signature(
                payment_link_id,
                payment_link_reference_id,
                payment_link_status,
                razorpay_signature
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # 2. Check payment status
    if payment_link_status != "paid":
        return {"status": "pending", "message": "Payment not completed"}
    
    # 3. Get payment data
    payment_ref = db.collection("payments").document(payment_link_id)
    payment_doc = payment_ref.get()
    if not payment_doc.exists:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    payment_data = payment_doc.to_dict()
    
    # 4. Check if already processed
    if payment_data.get("registration_id"):
        return {
            "status": "success",
            "message": "Registration already completed",
            "registration_id": payment_data.get("registration_id")
        }
    
    # 5. Get workshop details
    workshop_doc = db.collection("workshops").document(workshop_id).get()
    if not workshop_doc.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    workshop_data = workshop_doc.to_dict()
    
    # 6. Create registration
    reg_id = str(uuid.uuid4())
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
        "payment_id": razorpay_payment_id,
        "payment_link_id": payment_link_id,
        "amount": payment_data.get("amount"),
        "payment_status": "completed",
        "status": "confirmed",
        "registered_at": datetime.utcnow(),
        "payment_completed_at": datetime.utcnow()
    }
    
    db.collection(f"{workshop_id}_registrations").document(reg_id).set(reg_data)
    
    # Sync to Google Sheets
    background_tasks.add_task(
        _sync_workshop_to_google_sheets,
        reg_data
    )

    # Update user document with registered workshop
    try:
        # Find user by email
        users_query = db.collection("users").where("email", "==", payment_data.get("email")).limit(1).get()
        for user_doc in users_query:
            user_data = user_doc.to_dict()
            registered_workshops = user_data.get("registered_workshops", [])
            
            already_in_list = any(
                w.get("workshop_id") == workshop_id and w.get("registration_id") == reg_id
                for w in registered_workshops
            )
            
            if not already_in_list:
                from google.cloud.firestore import ArrayUnion
                db.collection("users").document(user_doc.id).update({
                    "registered_workshops": ArrayUnion([{
                        "workshop_id": workshop_id,
                        "registration_id": reg_id,
                        "registered_at": datetime.utcnow().isoformat()
                    }])
                })
    except Exception as e:
        print(f"Warning: Failed to update user document: {e}")
    
    # 7. Update payment record
    payment_ref.update({
        "status": "paid",
        "registration_id": reg_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
        "updated_at": datetime.utcnow()
    })
    
    return {
        "status": "success",
        "message": "Registration confirmed",
        "registration_id": reg_id
    }


@router.get("/{workshop_id}/check-email")
async def check_email_registered(workshop_id: str, email: str):
    """Check if an email is already registered for a workshop"""
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", email).limit(1).get()
    
    return {"registered": bool(list(existing_reg))}


@router.get("/{workshop_id}/check-registration")
async def check_user_registration(
    workshop_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Check if current user is already registered for a workshop"""
    if not current_user:
        return {"registered": False}
    
    email = current_user.get("email")
    if not email:
        return {"registered": False}
    
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", email).limit(1).get()
    
    return {"registered": bool(list(existing_reg))}


@router.post("/{workshop_id}/register")
async def register_workshop(
    workshop_id: str,
    registration: WorkshopRegistrationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Direct workshop registration with transaction ID"""
    
    workshop_ref = db.collection("workshops").document(workshop_id)
    workshop = workshop_ref.get()
    if not workshop.exists:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    workshop_data = workshop.to_dict()
    
    if workshop_data.get("status") != "open":
        raise HTTPException(status_code=400, detail="Workshop registration is closed")
    
    registrations_ref = db.collection(f"{workshop_id}_registrations")
    existing_reg = registrations_ref.where("email", "==", registration.email).limit(1).get()
    if list(existing_reg):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    reg_id = str(uuid.uuid4())
    reg_data = {
        "registration_id": reg_id,
        "workshop_id": workshop_id,
        "workshop_name": workshop_data.get("title", ""),
        "name": registration.name,
        "email": registration.email,
        "phone": registration.phone,
        "year": registration.year,
        "college_name": registration.college_name,
        "referral_id": registration.referral_id,
        "transaction_id": registration.transaction_id,
        "payment_status": "pending",
        "status": "pending",
        "registered_at": datetime.utcnow()
    }
    
    db.collection(f"{workshop_id}_registrations").document(reg_id).set(reg_data)
    
    # Sync to Google Sheets
    background_tasks.add_task(
        _sync_workshop_to_google_sheets,
        reg_data
    )

    try:
        users_query = db.collection("users").where("email", "==", registration.email).limit(1).get()
        for user_doc in users_query:
            # Check if already in user's registered_workshops to prevent duplicates
            user_data = user_doc.to_dict()
            registered_workshops = user_data.get("registered_workshops", [])
            
            already_in_list = any(
                w.get("workshop_id") == workshop_id and w.get("registration_id") == reg_id
                for w in registered_workshops
            )
            
            if not already_in_list:
                from google.cloud.firestore import ArrayUnion
                db.collection("users").document(user_doc.id).update({
                    "registered_workshops": ArrayUnion([{
                        "workshop_id": workshop_id,
                        "registration_id": reg_id,
                        "registered_at": datetime.utcnow().isoformat()
                    }])
                })
    except Exception as e:
        print(f"Warning: Failed to update user: {e}")
    
    return {"message": "Registration successful", "registration_id": reg_id}


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


def _sync_workshop_to_google_sheets(reg_data: dict):
    """Background task to sync workshop registration to Google Sheets"""
    try:
        print(f"📊 Starting Google Sheets sync for workshop registration: {reg_data.get('registration_id')}")
        sheets_service = get_google_sheets_service()
        
        if not sheets_service or not sheets_service.service:
            print(f"❌ Google Sheets service not available")
            return
        
        workshop_data = {
            'workshop_id': reg_data.get('workshop_id'),
            'workshop_name': reg_data.get('workshop_name'),
            'registration_id': reg_data.get('registration_id'),
            'registered_at': reg_data.get('registered_at').strftime('%Y-%m-%d %H:%M:%S') if reg_data.get('registered_at') else '',
            'status': reg_data.get('status', 'confirmed')
        }
        
        participant_data = {
            'college_name': reg_data.get('college_name'),
            'name': reg_data.get('name'),
            'email': reg_data.get('email'),
            'phone': reg_data.get('phone'),
            'year': reg_data.get('year'),
            'payment_id': reg_data.get('payment_id') or reg_data.get('transaction_id', ''),
            'amount': reg_data.get('amount', ''),
            'payment_status': reg_data.get('payment_status', 'pending')
        }
        
        result = sheets_service.append_workshop_registration(workshop_data, participant_data)
        if result:
            print(f"✅ Workshop registration synced to Google Sheets successfully")
        else:
            print(f"❌ Failed to sync workshop registration to Google Sheets")
        
    except Exception as e:
        print(f"❌ ERROR syncing workshop registration to Google Sheets: {str(e)}")
        import traceback
        traceback.print_exc()
