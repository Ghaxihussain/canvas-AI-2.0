from fastapi import APIRouter,HTTPException, Depends
from pydantic import BaseModel, EmailStr
import sys
import os
import json
from Backend.db.users import User
from Backend.db.database import get_db
from Backend.routes.helpers import create_access_token, create_refresh_token, verify_token
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))



class SignupPost(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginPost(BaseModel):
    email: EmailStr
    password: str


class RefreshPost(BaseModel):
    refresh_token: str
acc_router = APIRouter(prefix= "/accounts", tags= ["Account", "Users"])





@acc_router.post("/signup")
def signup(data: SignupPost, db: Session= Depends(get_db)):

    
    result = User.create(name = data.name, email= data.email, password= data.password, db = db)

    if result["code"] == 400:
        raise HTTPException(status_code=400, detail="Email already exists")
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail="Error Occurred while adding the user")
    
    return {"message": "User created successfully"}
            





@acc_router.post("/login")
def login(data: LoginPost, db: Session = Depends(get_db)):
    result = User.verify_user_password(email=data.email, password=data.password, db=db)
    if result["code"] == 401:
        raise HTTPException(status_code=401, detail=f"Password incorrect for user {data.email}")
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=f"No User {data.email}")
    if result["code"] == 200:
        return {
            "access_token": create_access_token(result["user_id"]),
            "refresh_token": create_refresh_token(result["user_id"]),
            "token_type": "bearer"
        }

@acc_router.post("/refresh")
def refresh(data: RefreshPost, db: Session = Depends(get_db)):
    user_id = verify_token(data.refresh_token, expected_type="refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = User.get_user_by_id(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}




