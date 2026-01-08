import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings
import json

def initialize_firebase():
    if not firebase_admin._apps:
        # Check if we have credentials in env vars
        if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
            
            # Basic validation to check if it's a Private Key (PEM format) or potentially an API Key (invalid for this)
            if not settings.FIREBASE_PRIVATE_KEY.strip().startswith("-----BEGIN PRIVATE KEY"):
                print("WARNING: FIREBASE_PRIVATE_KEY in .env does not look like a valid Service Account Private Key (PEM format).")
                print("It starts with: " + settings.FIREBASE_PRIVATE_KEY[:10] + "...")
                print("Please download a Service Account JSON from Firebase Console -> Project Settings -> Service Accounts.")
                print("Using default credential lookup instead (GOOGLE_APPLICATION_CREDENTIALS or gcloud auth).")
                
                # Try default initialization
                try:
                    firebase_admin.initialize_app()
                except Exception as e:
                    print(f"Failed to initialize Firebase with default credentials: {e}")
            else:
                # Handle private key formatting (replace \n with actual newlines)
                private_key = settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n')
                
                cred_dict = {
                    "type": "service_account",
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "private_key_id": "dummy_key_id", # Sometimes needed
                    "private_key": private_key,
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "client_id": "dummy_client_id",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL}"
                }
                
                try:
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                except ValueError as e:
                    print(f"Error loading Firebase credentials: {e}")
                    print("Check your FIREBASE_PRIVATE_KEY formatting in .env")
        else:
            # Fallback for local development if GOOGLE_APPLICATION_CREDENTIALS is set
            # or if using default credentials
             try:
                firebase_admin.initialize_app()
             except Exception as e:
                print(f"Failed to initialize Firebase: {e}")

    return firestore.client()

db = initialize_firebase()
