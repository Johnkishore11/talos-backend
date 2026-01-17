from pydantic import BaseModel, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, Any, List
from datetime import datetime

class WorkshopBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    title: str
    description: str
    main_description: Optional[str] = None
    rules: Optional[str] = None
    instructor: str
    date: str
    time: str
    duration: str
    venue: Optional[str] = None
    image_url: str
    max_participants: Optional[int] = None
    registration_fee: int
    status: str = "open"

    @model_validator(mode='before')
    @classmethod
    def map_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'id' -> 'workshop_id' if present
            if 'id' in data and 'workshop_id' not in data:
                data['workshop_id'] = data['id']
            
            # Map 'image' -> 'image_url'
            if 'image' in data and 'image_url' not in data:
                data['image_url'] = data['image']

            # Ensure status defaults to "open" if not present or empty
            if 'status' not in data or not data['status']:
                data['status'] = "open"
        return data

class WorkshopCreate(WorkshopBase):
    workshop_id: str

class Workshop(WorkshopBase):
    workshop_id: str
    created_at: Optional[datetime | str] = None


# Workshop Registration Request - Solo registration with payment
class WorkshopRegistrationRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    year: str  # e.g., "1st Year", "2nd Year", etc.
    college_name: str
    referral_id: Optional[str] = None  # Optional referral

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) != 10:
            raise ValueError('Phone number must be 10 digits')
        return cleaned


# For payment verification
class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    # Registration data to store after payment
    name: str
    email: EmailStr
    phone: str
    year: str
    college_name: str
    referral_id: Optional[str] = None


# Workshop Registration stored in Firestore
class WorkshopRegistration(BaseModel):
    registration_id: str
    workshop_id: str
    workshop_name: str
    
    # Participant Info
    name: str
    email: str
    phone: str
    year: str
    college_name: str
    referral_id: Optional[str] = None
    
    # Payment Info
    payment_id: str
    order_id: str
    amount: int
    payment_status: str  # "completed"
    
    # Metadata
    status: str  # "confirmed"
    registered_at: datetime
    payment_completed_at: Optional[datetime] = None
