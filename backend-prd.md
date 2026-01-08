TALOS Backend - Product Requirements Document (PRD)
1. Project Overview
1.1 Objective
Migrate database operations from frontend to a secure FastAPI backend to handle event/workshop registrations, Razorpay payment integration, and user data management while maintaining Firebase Authentication on the frontend.

1.2 Architecture
Frontend: Next.js (existing) - Handles UI, Firebase Auth

Backend: FastAPI (Python) - Handles database operations, payments, business logic

Database: Firebase Firestore (Admin SDK)

Payment: Razorpay

Auth Flow: Frontend Firebase token → Backend verification → API access

2. Database Schema
2.1 Collections Structure
Collection: users
{
  "uid": str,                    # Firebase UID (document ID)
  "name": str,
  "email": str,
  "profile_photo": str | None,
  "phone": str | None,
  "college": str | None,
  "created_at": timestamp,
  "last_login": timestamp
}


Collection: events
{
  "event_id": str,               # Document ID (slug)
  "title": str,
  "description": str,
  "category": str,
  "date": str,
  "time": str,
  "venue": str | None,
  "image_url": str,
  "max_participants": int | None,
  "registration_fee": int,       # 0 for free events
  "is_team_event": bool,
  "max_team_size": int | None,
  "status": str,                 # "open", "closed", "cancelled"
  "created_at": timestamp
}


Collection: workshops
{
  "workshop_id": str,            # Document ID (slug)
  "title": str,
  "description": str,
  "instructor": str,
  "date": str,
  "time": str,
  "duration": str,
  "venue": str | None,
  "image_url": str,
  "max_participants": int | None,
  "registration_fee": int,       # Required payment
  "status": str,                 # "open", "closed", "cancelled"
  "created_at": timestamp
}


Collection: event_registrations
{
  "registration_id": str,        # Auto-generated document ID
  "user_id": str,                # Firebase UID
  "event_id": str,
  "registration_type": str,      # "solo" or "team"
  "team_name": str | None,
  "team_members": [              # Array of team member objects
    {
      "name": str,
      "email": str,
      "phone": str | None
    }
  ],
  "status": str,                 # "confirmed", "cancelled"
  "registered_at": timestamp
}


Collection: workshop_registrations
{
  "registration_id": str,        # Auto-generated document ID
  "user_id": str,
  "workshop_id": str,
  "payment_id": str,             # Razorpay payment_id
  "order_id": str,               # Razorpay order_id
  "amount": int,
  "payment_status": str,         # "pending", "completed", "failed"
  "status": str,                 # "confirmed", "cancelled"
  "registered_at": timestamp,
  "payment_completed_at": timestamp | None
}


Collection: payments
{
  "payment_id": str,             # Razorpay payment_id (document ID)
  "order_id": str,               # Razorpay order_id
  "user_id": str,
  "workshop_id": str,
  "registration_id": str,
  "amount": int,
  "currency": str,               # "INR"
  "status": str,                 # "created", "authorized", "captured", "failed"
  "razorpay_signature": str | None,
  "created_at": timestamp,
  "updated_at": timestamp
}


3. API Endpoints
3.1 Authentication Middleware
All endpoints (except webhooks) require Firebase ID token in header:

Authorization: Bearer <firebase_id_token>


3.2 User Endpoints
GET /api/user/profile
Get current user profile

Response: User object

PUT /api/user/profile
Update user profile (phone, college)

Body: { phone, college }

Response: Updated user object

3.3 Event Endpoints
GET /api/events
Get all events (public)

Query params: status=open (optional)

Response: Array of events

GET /api/events/{event_id}
Get single event details

Response: Event object

POST /api/events/{event_id}/register
Register for free event

Body:

{
  "registration_type": "solo" | "team",
  "team_name": str (optional),
  "team_members": [
    { "name": str, "email": str, "phone": str }
  ] (optional)
}

Copy

Insert at cursor
Response: Registration confirmation + email sent

GET /api/user/events
Get user's event registrations

Response: Array of registrations

3.4 Workshop Endpoints
GET /api/workshops
Get all workshops (public)

Query params: status=open (optional)

Response: Array of workshops

GET /api/workshops/{workshop_id}
Get single workshop details

Response: Workshop object

POST /api/workshops/{workshop_id}/create-order
Create Razorpay order for workshop

Response:

{
  "order_id": str,
  "amount": int,
  "currency": "INR",
  "key_id": str  // Razorpay key for frontend
}

Copy

Insert at cursor
json
POST /api/workshops/{workshop_id}/verify-payment
Verify payment and complete registration

Body:

{
  "razorpay_order_id": str,
  "razorpay_payment_id": str,
  "razorpay_signature": str
}

Copy

Insert at cursor
json
Response: Registration confirmation + email sent

GET /api/user/workshops
Get user's workshop registrations

Response: Array of registrations

3.5 Webhook Endpoints
POST /api/webhooks/razorpay
Handle Razorpay payment webhooks

Verify webhook signature

Update payment status

Send confirmation email on success

4. Technical Implementation
4.1 Tech Stack
Framework: FastAPI

Database: Firebase Admin SDK (Firestore)

Payment: Razorpay Python SDK

Email: SMTP (Gmail) or SendGrid

Auth: Firebase Admin SDK (token verification)

Environment: Python 3.10+

4.2 Key Dependencies
fastapi
uvicorn
firebase-admin
razorpay
pydantic
python-dotenv
python-multipart
aiosmtplib (for email)

Copy

Insert at cursor
4.3 Environment Variables
# Firebase
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=

# App
FRONTEND_URL=http://localhost:3000

Copy

Insert at cursor
env
5. Security Requirements
5.1 Authentication
Verify Firebase ID token on every protected endpoint

Extract user UID from verified token

No role-based access control (all authenticated users have same permissions)

5.2 Payment Security
Verify Razorpay signature on payment verification

Verify webhook signature on webhook endpoints

Store payment records for audit trail

5.3 Data Validation
Validate all input using Pydantic models

Sanitize user inputs

Check event/workshop capacity before registration

6. Email Notifications
6.1 Event Registration Email
Subject: "Registration Confirmed - {Event Name}"

Content: Event details, date, venue, QR code (optional)

6.2 Workshop Payment Success Email
Subject: "Payment Successful - {Workshop Name}"

Content: Workshop details, payment receipt, registration confirmation

6.3 Workshop Payment Failed Email
Subject: "Payment Failed - {Workshop Name}"

Content: Failure reason, retry instructions

7. Frontend Integration Changes
7.1 Required Changes
Remove direct Firestore calls from frontend

Create API service layer for backend communication

Send Firebase ID token with every API request

Integrate Razorpay checkout on workshop registration

Handle payment verification flow

7.2 API Service Example
// lib/api.ts
const getIdToken = async () => {
  const user = auth.currentUser;
  return await user?.getIdToken();
};

export const apiClient = {
  registerEvent: async (eventId, data) => {
    const token = await getIdToken();
    const response = await fetch(`${API_URL}/api/events/${eventId}/register`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};

Copy

Insert at cursor
typescript
8. Project Structure
TALOS_b/talos-backend/
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Environment config
│   ├── dependencies.py         # Auth middleware
│   ├── models/
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── workshop.py
│   │   └── payment.py
│   ├── routes/
│   │   ├── user.py
│   │   ├── events.py
│   │   ├── workshops.py
│   │   └── webhooks.py
│   ├── services/
│   │   ├── firebase_service.py
│   │   ├── razorpay_service.py
│   │   └── email_service.py
│   └── utils/
│       └── validators.py
├── requirements.txt
├── .env
└── README.md

Copy

Insert at cursor
9. Development Phases
Phase 1: Setup & Core Infrastructure
FastAPI project setup

Firebase Admin SDK integration

Authentication middleware

Database models & schemas

Phase 2: Event Management
Event CRUD endpoints

Event registration (free)

Email notifications for events

Phase 3: Workshop & Payment Integration
Workshop CRUD endpoints

Razorpay order creation

Payment verification

Workshop registration flow

Phase 4: Webhooks & Email
Razorpay webhook handler

Email service implementation

Payment confirmation emails

Phase 5: Frontend Integration
Update frontend to use backend APIs

Remove direct Firestore calls

Razorpay checkout integration

10. Testing Requirements
Unit tests for all services

Integration tests for payment flow

Test webhook handling with Razorpay test mode

Test email delivery

Load testing for concurrent registrations

11. Success Metrics
All database operations moved to backend

Secure payment processing with Razorpay

Email notifications working reliably

Firebase token verification on all requests

Zero direct Firestore access from frontend