from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import os
from fastapi import Request, Depends, HTTPException
from Backend.db.database import get_db
from sqlalchemy.orm import Session
from Backend.db.users import User

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str) -> str:
    payload = {
        "user": user_id,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "user": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return {"code": 401}
        return {"code": 200, "user_id": payload.get("user")}
    except JWTError:
        return {"code": 401}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = verify_token(token, expected_type="access")
    if result["code"] != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = User.get_user_by_id(user_id=result["user_id"], db=db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user