from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app.auth.firebase import create_user, verify_firebase_token

router = APIRouter()

class UserSignup(BaseModel):
    email: str
    password: str

class AuthToken(BaseModel):
    token: str

@router.post("/signup")
async def signup(user: UserSignup):
    """Sign up a new user with Firebase Authentication."""
    try:
        user_data = create_user(user.email, user.password)
        return {"message": "User created successfully", "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify-token")
async def verify_token(authorization: str = Header(...)):
    """Verifies Firebase ID Token from headers"""
    token = authorization.replace("Bearer ", "")
    user_data = verify_firebase_token(token)
    if user_data:
        return {"message": "Token is valid", "user": user_data}
    raise HTTPException(status_code=401, detail="Invalid token")
