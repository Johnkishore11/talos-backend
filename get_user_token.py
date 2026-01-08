import os
import requests
import firebase_admin
from firebase_admin import auth
from dotenv import load_dotenv
from app.services.firebase_service import initialize_firebase
import time

# Load env vars
load_dotenv()

# Configuration
WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

if not WEB_API_KEY:
    print("Error: FIREBASE_WEB_API_KEY not found in .env")
    exit(1)

# Initialize Firebase Admin
try:
    if not firebase_admin._apps:
        initialize_firebase()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit(1)

def get_uid_by_email(email):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except auth.UserNotFoundError:
        print(f"User with email {email} not found.")
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def get_id_token(uid):
    try:
        # 1. Create a Custom Token using Admin SDK
        custom_token = auth.create_custom_token(uid)
        custom_token_str = custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token

        # 2. Exchange Custom Token for ID Token using Firebase REST API
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={WEB_API_KEY}"
        payload = {
            "token": custom_token_str,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            id_token = response.json().get("idToken")
            return id_token
        else:
            print(f"Error exchanging token: {response.text}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    TARGET_EMAIL = "taloscit72@gmail.com"
    
    print(f"Looking up UID for email: {TARGET_EMAIL}...")
    uid = get_uid_by_email(TARGET_EMAIL)
    
    if uid:
        print(f"Found UID: {uid}")
        print(f"Generating ID Token...")
        token = get_id_token(uid)
        
        if token:
            print("\n=== YOUR ID TOKEN (Bearer) ===")
            print(token)
            
            print("\nWaiting 15 seconds to allow for clock skew...")
            time.sleep(15)

            # Verify against backend immediately
            print("\n=== Verifying against Backend (GET /api/user/profile) ===")
            try:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get("http://localhost:8000/api/user/profile", headers=headers)
                print(f"Status Code: {resp.status_code}")
                if resp.status_code == 200:
                    print("Response: Profile found!")
                    print(resp.json())
                elif resp.status_code == 404:
                    print("Response: Auth success (404 Profile not found - User doc missing in DB)")
                elif resp.status_code == 401:
                    print("Response: Auth Failed (401 Unauthorized)")
                    print(resp.text)
                else:
                    print(f"Response: {resp.text}")
            except Exception as e:
                print(f"Failed to connect to backend: {e}")

    else:
        print("Could not proceed without UID.")