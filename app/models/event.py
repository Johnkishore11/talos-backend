from pydantic import BaseModel, model_validator, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class EventOrganiser(BaseModel):
    name: str
    contact: List[str] = []


class EventBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    title: str
    description: str
    main_description: Optional[str] = None
    rules: Optional[str] = None
    category: str
    date: str
    time: str
    venue: Optional[str] = None
    image_url: str
    max_participants: Optional[int] = None
    min_team_size: int = 2
    max_team_size: int = 4
    registration_fee: int = 0
    status: str = "open"
    organiser: Optional[EventOrganiser] = None

    @model_validator(mode='before')
    @classmethod
    def map_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'id' -> 'event_id'
            if 'id' in data and 'event_id' not in data:
                data['event_id'] = data['id']
            
            # Map 'image' -> 'image_url'
            if 'image' in data and 'image_url' not in data:
                data['image_url'] = data['image']
                
            # Map 'venue' -> 'location' (and vice versa if needed)
            if 'location' in data and 'venue' not in data:
                data['venue'] = data['location']

            # Map 'minTeamSize' -> 'min_team_size'
            if 'minTeamSize' in data and 'min_team_size' not in data:
                data['min_team_size'] = data['minTeamSize']

            # Map 'maxTeamSize' -> 'max_team_size'
            if 'maxTeamSize' in data and 'max_team_size' not in data:
                data['max_team_size'] = data['maxTeamSize']

            # Ensure status defaults to "open" if not present or empty
            if 'status' not in data or not data['status']:
                data['status'] = "open"

            # Handle missing 'time' but present 'date' with time component
            if 'time' not in data:
                if 'date' in data and isinstance(data['date'], str) and 'T' in data['date']:
                    try:
                        # Parse ISO format: 2026-02-14T09:00:00
                        dt = datetime.fromisoformat(data['date'])
                        data['time'] = dt.strftime("%I:%M %p") # e.g. 09:00 AM
                        # Normalize date to YYYY-MM-DD
                        data['date'] = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        data['time'] = "09:00 AM" # Fallback
                elif 'date' in data and isinstance(data['date'], str):
                     # If date is just a string without T, maybe we can't extract time easily
                     data['time'] = "09:00 AM" # Fallback
        return data

class EventCreate(EventBase):
    event_id: str

class Event(EventBase):
    event_id: str
    created_at: Optional[datetime | str] = None


# Team Member model for event registration (1-3 members)
class TeamMember(BaseModel):
    name: str
    email: EmailStr
    phone: str

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Remove any spaces or dashes
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 10:
            raise ValueError('Phone number must be 10 digits')
        return cleaned


# Event Registration Request - Team based, FREE registration
class EventRegistrationRequest(BaseModel):
    # Team Info
    team_name: str  # Required and must be unique per event
    
    # Team Leader Info
    leader_name: str
    leader_email: EmailStr
    leader_phone: str
    leader_year: str  # e.g., "1st Year", "2nd Year", etc.
    college_name: str
    referral_id: Optional[str] = None  # Optional referral
    transaction_id: Optional[str] = None  # Transaction ID for paid events
    
    # Team Members (1-3 members)
    members: List[TeamMember]

    @field_validator('leader_phone')
    @classmethod
    def validate_leader_phone(cls, v: str) -> str:
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 10:
            raise ValueError('Phone number must be 10 digits')
        return cleaned

    @field_validator('members')
    @classmethod
    def validate_members(cls, v: List[TeamMember]) -> List[TeamMember]:
        if len(v) > 3:
            raise ValueError('Maximum 3 team members allowed')
        return v


# Event Registration stored in Firestore
class EventRegistration(BaseModel):
    registration_id: str
    event_id: str
    event_name: str
    
    # Team Info
    team_name: str
    
    # Team Leader Info
    leader_name: str
    leader_email: str
    leader_phone: str
    leader_year: str
    college_name: str
    referral_id: Optional[str] = None
    transaction_id: Optional[str] = None
    
    # Team Members
    members: List[TeamMember]
    
    # Metadata
    status: str  # "confirmed"
    registered_at: datetime
