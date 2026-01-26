from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from app.dependencies import get_current_user, get_optional_user
from app.services.firebase_service import db
from app.services.email_service import send_event_registration_email
from app.services.google_sheets_service import get_google_sheets_service
from app.models.event import Event, EventRegistration, EventRegistrationRequest
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter()

@router.get("", response_model=List[Event])
@router.get("/", response_model=List[Event])
async def get_events(status: Optional[str] = None):
    try:
        if status and status != "all":
            docs = db.collection("events").where("status", "==", status).stream()
        else:
            docs = db.collection("events").stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(data)
            
        return results
    except Exception as e:
        print(f"ERROR in get_events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str):
    doc = db.collection("events").document(event_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    return doc.to_dict()


@router.post("/{event_id}/register")
async def register_event(
    event_id: str,
    registration: EventRegistrationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Register a team for an event (FREE or PAID registration).
    Stores registration in {event_id}_registrations collection.
    Team name must be unique per event.
    For paid events, transaction_id is required.
    """
    
    # 1. Check if event exists
    event_ref = db.collection("events").document(event_id)
    # event_doc = event_ref.get() # Blocking
    event_doc = await run_in_threadpool(event_ref.get)
    
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_data = event_doc.to_dict()
    
    # 2. Check if event is open for registration (default to "open" if not set)
    event_status = event_data.get("status", "open") or "open"
    if event_status != "open":
        raise HTTPException(status_code=400, detail="Event registration is closed")
    
    # 3. Check if event has registration fee and transaction_id is required
    registration_fee = event_data.get("registration_fee", 0)
    if registration_fee > 0 and not registration.transaction_id:
        raise HTTPException(status_code=400, detail="Transaction ID is required for paid events")
    
    # 4. Validate team size
    min_team_size = event_data.get("min_team_size", 2)  # Default: leader + 1 member
    max_team_size = event_data.get("max_team_size", 5)  # Default: leader + 4 members
    
    total_members = len(registration.members) + 1  # +1 for leader
    if total_members < min_team_size:
        raise HTTPException(
            status_code=400, 
            detail=f"Team must have at least {min_team_size} members (including leader)"
        )
    if total_members > max_team_size:
        raise HTTPException(
            status_code=400, 
            detail=f"Team cannot have more than {max_team_size} members (including leader)"
        )
    
    # 5. Check if team name is unique for this event
    registrations_ref = db.collection(f"{event_id}_registrations")
    # existing_team = registrations_ref.where("team_name", "==", registration.team_name).limit(1).get() # Blocking
    existing_team = await run_in_threadpool(
        registrations_ref.where("team_name", "==", registration.team_name).limit(1).get
    )
    if list(existing_team):
        raise HTTPException(status_code=400, detail="Team name already exists for this event. Please choose a different name.")
    
    # 6. Check if leader email is already registered for this event
    # existing_leader = registrations_ref.where("leader_email", "==", registration.leader_email).limit(1).get() # Blocking
    existing_leader = await run_in_threadpool(
        registrations_ref.where("leader_email", "==", registration.leader_email).limit(1).get
    )
    if list(existing_leader):
        raise HTTPException(status_code=400, detail="You are already registered for this event")
    
    # 7. Check if any team member email is already registered as leader
    for member in registration.members:
        # existing_member = registrations_ref.where("leader_email", "==", member.email).limit(1).get() # Blocking
        existing_member = await run_in_threadpool(
            registrations_ref.where("leader_email", "==", member.email).limit(1).get
        )
        if list(existing_member):
            raise HTTPException(status_code=400, detail=f"Email {member.email} is already registered for this event")

    # 8. Create Registration
    reg_id = str(uuid.uuid4())
    reg_data = {
        "registration_id": reg_id,
        "event_id": event_id,
        "event_name": event_data.get("title", ""),
        
        # Team Info
        "team_name": registration.team_name,
        
        # Leader Info
        "leader_name": registration.leader_name,
        "leader_email": registration.leader_email,
        "leader_phone": registration.leader_phone,
        "leader_year": registration.leader_year,
        "college_name": registration.college_name,
        "referral_id": registration.referral_id,
        "transaction_id": registration.transaction_id,
        
        # Team Members
        "members": [member.dict() for member in registration.members],
        
        # Metadata
        "status": "confirmed",
        "registered_at": datetime.utcnow()
    }
    
    # Store in event-specific collection
    # registrations_ref.document(reg_id).set(reg_data) # Blocking
    await run_in_threadpool(registrations_ref.document(reg_id).set, reg_data)
    
    # Update user document with registered event
    try:
        user_ref = db.collection("users").document(current_user["uid"])
        # user_doc = user_ref.get() # Blocking
        user_doc = await run_in_threadpool(user_ref.get)
        
        if user_doc.exists:
            # Check if already in user's registered_events to prevent duplicates
            user_data = user_doc.to_dict()
            registered_events = user_data.get("registered_events", [])
            
            # Check if this event is already in the list
            already_in_list = any(
                e.get("event_id") == event_id and e.get("registration_id") == reg_id 
                for e in registered_events
            )
            
            if not already_in_list:
                from google.cloud.firestore import ArrayUnion
                # user_ref.update(...) # Blocking
                await run_in_threadpool(
                    user_ref.update,
                    {
                        "registered_events": ArrayUnion([{
                            "event_id": event_id,
                            "registration_id": reg_id,
                            "team_name": registration.team_name,
                            "registered_at": datetime.utcnow().isoformat()
                        }])
                    }
                )
    except Exception as e:
        print(f"Warning: Failed to update user document: {e}")
    
    # 8. Send confirmation email
    if registration.leader_email:
        background_tasks.add_task(
            send_event_registration_email, 
            registration.leader_email, 
            event_data.get("title"), 
            event_data.get("date")
        )
    
    # 9. Sync to Google Sheets (background task)
    background_tasks.add_task(
        _sync_event_to_google_sheets,
        reg_data,
        registration.members
    )

    # Determine status based on payment requirement
    response_message = "Registration successful"
    if registration_fee > 0:
        response_message = "Registration successful! Your registration is pending verification."

    return {
        "message": response_message, 
        "registration_id": reg_id,
        "team_name": registration.team_name
    }


@router.get("/{event_id}/check-team-name")
async def check_team_name(event_id: str, team_name: str):
    """Check if a team name is available for an event"""
    registrations_ref = db.collection(f"{event_id}_registrations")
    existing_team = registrations_ref.where("team_name", "==", team_name).limit(1).get()
    
    return {"available": not list(existing_team)}


@router.get("/{event_id}/check-registration")
async def check_user_registration(
    event_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Check if current user is already registered for an event"""
    if not current_user:
        return {"registered": False}
    
    email = current_user.get("email")
    if not email:
        return {"registered": False}
    
    registrations_ref = db.collection(f"{event_id}_registrations")
    existing_reg = registrations_ref.where("leader_email", "==", email).limit(1).get()
    
    return {"registered": bool(list(existing_reg))}


@router.get("/{event_id}/registrations")
async def get_event_registrations(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all registrations for an event (admin use)"""
    # Check if event exists
    event_ref = db.collection("events").document(event_id)
    if not event_ref.get().exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    registrations_ref = db.collection(f"{event_id}_registrations")
    docs = registrations_ref.stream()
    
    return [doc.to_dict() for doc in docs]


def _sync_event_to_google_sheets(reg_data: dict, members: list):
    """Background task to sync event registration to Google Sheets"""
    try:
        print(f"📊 Starting Google Sheets sync for event registration: {reg_data.get('registration_id')}")
        sheets_service = get_google_sheets_service()
        
        if not sheets_service or not sheets_service.service:
            print(f"❌ Google Sheets service not available")
            return
        
        leader_data = {
            'college_name': reg_data.get('college_name'),
            'name': reg_data.get('leader_name'),
            'email': reg_data.get('leader_email'),
            'phone': reg_data.get('leader_phone'),
            'year': reg_data.get('leader_year')
        }
        
        event_data = {
            'event_id': reg_data.get('event_id'),
            'event_name': reg_data.get('event_name'),
            'registration_id': reg_data.get('registration_id'),
            'team_name': reg_data.get('team_name'),
            'referral_id': reg_data.get('referral_id'),
            'registered_at': reg_data.get('registered_at').strftime('%Y-%m-%d %H:%M:%S') if reg_data.get('registered_at') else '',
            'status': reg_data.get('status', 'confirmed')
        }
        
        # Convert member dicts to formatted list
        members_list = [
            {
                'name': m.get('name') if isinstance(m, dict) else m.name,
                'email': m.get('email') if isinstance(m, dict) else m.email,
                'phone': m.get('phone') if isinstance(m, dict) else m.phone
            }
            for m in members
        ]
        
        result = sheets_service.append_event_registration(event_data, leader_data, members_list)
        if result:
            print(f"✅ Event registration synced to Google Sheets successfully")
        else:
            print(f"❌ Failed to sync event registration to Google Sheets")
        
    except Exception as e:
        print(f"❌ ERROR syncing event registration to Google Sheets: {str(e)}")
        import traceback
        traceback.print_exc()
