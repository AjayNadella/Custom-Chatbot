import firebase_admin
from firebase_admin import auth, credentials
import os

firebase_json_path = os.path.abspath("app/auth/custom-chatbot-auth-firebase-adminsdk-fbsvc-dfceec2aae.json")
cred = credentials.Certificate(firebase_json_path)
firebase_admin.initialize_app(cred)

def create_user(email: str, password: str):
    """Creates a new user in Firebase Authentication"""
    user = auth.create_user(email=email, password=password)
    return {"uid": user.uid, "email": user.email}

def verify_firebase_token(token: str):
    """Verifies Firebase ID token and returns user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        return None
