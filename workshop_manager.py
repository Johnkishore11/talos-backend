import sys
from datetime import datetime
from app.services.firebase_service import db
from workshops_data import WORKSHOPS

def add_workshop(workshop_key):
    """Add a new workshop to the database"""
    if workshop_key not in WORKSHOPS:
        print(f"X Workshop '{workshop_key}' not found in workshops_data.py")
        print(f"Available workshops: {', '.join(WORKSHOPS.keys())}")
        return
    
    workshop_data = WORKSHOPS[workshop_key].copy()
    workshop_data['created_at'] = datetime.utcnow()
    db.collection("workshops").document(workshop_data["workshop_id"]).set(workshop_data)
    print(f"+ Added workshop: {workshop_data['title']}")

def delete_workshop(workshop_id):
    """Delete a workshop from the database"""
    doc = db.collection("workshops").document(workshop_id).get()
    if doc.exists:
        title = doc.to_dict().get('title', workshop_id)
        db.collection("workshops").document(workshop_id).delete()
        print(f"- Deleted workshop: {title}")
    else:
        print(f"X Workshop not found: {workshop_id}")

def list_workshops():
    """List all workshops in the database"""
    workshops = db.collection("workshops").stream()
    print("\n=== Current Workshops ===")
    count = 0
    for workshop in workshops:
        data = workshop.to_dict()
        count += 1
        print(f"\n{count}. {data.get('title')}")
        print(f"   ID: {workshop.id}")
        print(f"   Fee: Rs.{data.get('registration_fee')}")
        print(f"   Status: {data.get('status')}")
    print(f"\nTotal workshops: {count}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python workshop_manager.py list")
        print("  python workshop_manager.py delete <workshop_id>")
        print("  python workshop_manager.py add <workshop_key>")
        print(f"\nAvailable workshop keys: {', '.join(WORKSHOPS.keys())}")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_workshops()
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Please provide workshop_id")
            sys.exit(1)
        delete_workshop(sys.argv[2])
        list_workshops()
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: Please provide workshop_key")
            print(f"Available workshops: {', '.join(WORKSHOPS.keys())}")
            sys.exit(1)
        add_workshop(sys.argv[2])
        list_workshops()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
