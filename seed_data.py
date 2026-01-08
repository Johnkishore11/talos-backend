import firebase_admin
from firebase_admin import credentials, firestore
from app.services.firebase_service import db
from datetime import datetime

def seed_data():
    # Seed Events
    events = [
        {
            "event_id": "tech-quiz",
            "title": "Tech Quiz 2026",
            "description": "Showcase your technical knowledge in our annual tech quiz competition.",
            "category": "Technical",
            "date": "2026-03-15",
            "time": "10:00 AM",
            "venue": "Main Auditorium",
            "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3",
            "max_participants": 100,
            "registration_fee": 0,
            "is_team_event": True,
            "max_team_size": 2,
            "status": "open",
            "created_at": datetime.utcnow()
        },
        {
            "event_id": "hackathon",
            "title": "Code Burst",
            "description": "24-hour hackathon to solve real-world problems.",
            "category": "Coding",
            "date": "2026-03-16",
            "time": "09:00 AM",
            "venue": "IT Lab 1",
            "image_url": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d",
            "max_participants": 50,
            "registration_fee": 100,
            "is_team_event": True,
            "max_team_size": 4,
            "status": "open",
            "created_at": datetime.utcnow()
        }
    ]

    for event in events:
        db.collection("events").document(event["event_id"]).set(event)
        print(f"Seeded event: {event['title']}")

    # Seed Workshops
    workshops = [
        {
            "workshop_id": "ai-workshop",
            "title": "Introduction to AI & ML",
            "description": "Learn the basics of Artificial Intelligence and Machine Learning.",
            "instructor": "Dr. Smith",
            "date": "2026-03-20",
            "time": "11:00 AM",
            "duration": "4 Hours",
            "venue": "Seminar Hall",
            "image_url": "https://images.unsplash.com/photo-1550751827-4bd3774c3f58b",
            "max_participants": 30,
            "registration_fee": 500,
            "status": "open",
            "created_at": datetime.utcnow()
        }
    ]

    for workshop in workshops:
        db.collection("workshops").document(workshop["workshop_id"]).set(workshop)
        print(f"Seeded workshop: {workshop['title']}")

    # Verification
    events_count = len(list(db.collection("events").stream()))
    print(f"Total events in DB: {events_count}")

if __name__ == "__main__":
    seed_data()
