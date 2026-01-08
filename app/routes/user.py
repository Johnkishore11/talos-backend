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
    doc_ref = db.collection("users").document(uid)
    doc = doc_ref.get()
    
    if not doc.exists:
        # If user doesn't exist in DB but has a valid Firebase Token, maybe create? 
        # Or return 404. PRD assumes user management. 
        # Let's return 404 for now or minimal info.
        raise HTTPException(status_code=404, detail="User profile not found")
        
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
    Get all event registrations for the current user.
    Searches across all event-specific collections ({event_id}_registrations)
    by the user's email.
    """
    user_email = current_user.get("email")
    if not user_email:
        return []
    
    all_registrations = []
    
    # Get all events to know which collections to search
    events_docs = db.collection("events").stream()
    
    for event_doc in events_docs:
        event_id = event_doc.id
        event_data = event_doc.to_dict()
        
        # Search in the event-specific registrations collection
        registrations_ref = db.collection(f"{event_id}_registrations")
        
        # Search by leader_email (team leader)
        leader_regs = registrations_ref.where("leader_email", "==", user_email).stream()
        
        for reg_doc in leader_regs:
            reg_data = reg_doc.to_dict()
            reg_data["event_name"] = event_data.get("title", event_id)
            reg_data["event_date"] = event_data.get("date", "")
            reg_data["event_venue"] = event_data.get("venue", "")
            all_registrations.append(reg_data)
    
    return all_registrations

@router.get("/workshops")
async def get_user_workshops(current_user: dict = Depends(get_current_user)):
    """
    Get all workshop registrations for the current user.
    Searches across all workshop-specific collections ({workshop_id}_registrations)
    by the user's email.
    """
    user_email = current_user.get("email")
    if not user_email:
        return []
    
    all_registrations = []
    
    # Get all workshops to know which collections to search
    workshops_docs = db.collection("workshops").stream()
    
    for workshop_doc in workshops_docs:
        workshop_id = workshop_doc.id
        workshop_data = workshop_doc.to_dict()
        
        # Search in the workshop-specific registrations collection
        registrations_ref = db.collection(f"{workshop_id}_registrations")
        
        # Search by email
        user_regs = registrations_ref.where("email", "==", user_email).where("status", "==", "confirmed").stream()
        
        for reg_doc in user_regs:
            reg_data = reg_doc.to_dict()
            reg_data["workshop_name"] = workshop_data.get("title", workshop_id)
            reg_data["workshop_date"] = workshop_data.get("date", "")
            reg_data["workshop_venue"] = workshop_data.get("venue", "")
            reg_data["instructor"] = workshop_data.get("instructor", "")
            all_registrations.append(reg_data)
    
    return all_registrations
