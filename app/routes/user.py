from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies import get_current_user
from app.services.firebase_service import db
from app.models.user import User, UserUpdate
from app.models.event import EventRegistration
from app.models.workshop import WorkshopRegistration
from typing import List

router = APIRouter()

@router.get("/profile", response_model=User)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    uid = current_user["uid"]
    email = current_user.get("email")
    doc_ref = db.collection("users").document(uid)
    doc = doc_ref.get()
    
    if not doc.exists:
        # Create a basic user profile if it doesn't exist
        from datetime import datetime
        user_data = {
            "uid": uid,
            "email": email or "",
            "name": current_user.get("name", ""),
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat()
        }
        doc_ref.set(user_data)
        return user_data
        
    return doc.to_dict()

@router.put("/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    uid = current_user["uid"]
    doc_ref = db.collection("users").document(uid)
    
    # Check if user exists
    if not doc_ref.get().exists:
         raise HTTPException(status_code=404, detail="User profile not found")

    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        doc_ref.update(update_data)
        
    return doc_ref.get().to_dict()

@router.get("/events")
async def get_user_events(current_user: dict = Depends(get_current_user)):
    """
    Get all event registrations for the current user from their user document.
    """
    uid = current_user.get("uid")
    if not uid:
        return []
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return []
        
        user_data = user_doc.to_dict()
        registered_events = user_data.get("registered_events", [])
        
        # Fetch full event details for each registration
        all_registrations = []
        for reg_ref in registered_events:
            event_id = reg_ref.get("event_id")
            registration_id = reg_ref.get("registration_id")
            
            if not event_id or not registration_id:
                continue
            
            # Get event details
            event_doc = db.collection("events").document(event_id).get()
            event_data = event_doc.to_dict() if event_doc.exists else {}
            
            # Get registration details
            reg_doc = db.collection(f"{event_id}_registrations").document(registration_id).get()
            if reg_doc.exists:
                reg_data = reg_doc.to_dict()
                reg_data["registration_id"] = registration_id
                reg_data["event_name"] = event_data.get("title", event_id)
                reg_data["event_date"] = event_data.get("date", "")
                reg_data["event_venue"] = event_data.get("venue", "")
                all_registrations.append(reg_data)
        
        return all_registrations
    except Exception as e:
        print(f"Error fetching user events: {e}")
        return []

@router.get("/workshops")
async def get_user_workshops(current_user: dict = Depends(get_current_user)):
    """
    Get all workshop registrations for the current user from their user document.
    """
    uid = current_user.get("uid")
    if not uid:
        return []
    
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return []
        
        user_data = user_doc.to_dict()
        registered_workshops = user_data.get("registered_workshops", [])
        
        # Fetch full workshop details for each registration
        all_registrations = []
        for reg_ref in registered_workshops:
            workshop_id = reg_ref.get("workshop_id")
            registration_id = reg_ref.get("registration_id")
            
            if not workshop_id or not registration_id:
                continue
            
            # Get workshop details
            workshop_doc = db.collection("workshops").document(workshop_id).get()
            workshop_data = workshop_doc.to_dict() if workshop_doc.exists else {}
            
            # Get registration details
            reg_doc = db.collection(f"{workshop_id}_registrations").document(registration_id).get()
            if reg_doc.exists:
                reg_data = reg_doc.to_dict()
                reg_data["registration_id"] = registration_id
                reg_data["workshop_name"] = workshop_data.get("title", workshop_id)
                reg_data["workshop_date"] = workshop_data.get("date", "")
                reg_data["workshop_venue"] = workshop_data.get("venue", "")
                reg_data["instructor"] = workshop_data.get("instructor", "")
                all_registrations.append(reg_data)
        
        return all_registrations
    except Exception as e:
        print(f"Error fetching user workshops: {e}")
        return []
