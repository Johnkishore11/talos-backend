from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Payment(BaseModel):
    payment_id: str
    order_id: str
    user_id: str
    workshop_id: str
    registration_id: str
    amount: int
    currency: str = "INR"
    status: str
    razorpay_signature: Optional[str] = None
    created_at: datetime
    updated_at: datetime
