from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, EmailStr
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Backend.db.users import User
from Backend.db.database import get_db
from Backend.routes.helpers import create_access_token, create_refresh_token, verify_token, get_current_user
from sqlalchemy.orm import Session


class SignupPost(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginPost(BaseModel):
    email: EmailStr
    password: str

class DeleteUserPatch(BaseModel):
    password: str


class UpdateProfilePatch(BaseModel):
    oname: str
    oemail:EmailStr
    name: str
    email: EmailStr


class ChangePasswordPatch(BaseModel):
    old_password: str
    new_password: str

    
acc_router = APIRouter(prefix="/accounts", tags=["Account", "Users"])


@acc_router.post("/signup")
def signup(data: SignupPost, db: Session = Depends(get_db)):
    result = User.create(name=data.name, email=data.email, password=data.password, db=db)
    if result["code"] == 400:
        raise HTTPException(status_code=400, detail="Email already exists")
    if result["code"] != 200:
        raise HTTPException(status_code=500, detail="Error creating user")
    return {"message": "User created successfully"}


@acc_router.post("/login")
def login(data: LoginPost, response: Response, db: Session = Depends(get_db)):
    result = User.verify_user_password(email=data.email, password=data.password, db=db)
    if result == False:
        raise HTTPException(status_code=404, detail="Incorrect password or User doesnt exists")
    

    response.set_cookie(key="access_token", value=create_access_token(result), httponly=True)
    response.set_cookie(key="refresh_token", value=create_refresh_token(result), httponly=True)
    return {"message": "Logged in successfully"}


@acc_router.post("/refresh")
def refresh(response: Response, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    result = verify_token(token, expected_type="refresh")
    if result["code"] != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user = User.get_user_by_id(user_id=result["user_id"], db=db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    response.set_cookie(key="access_token", value=create_access_token(str(user.id)), httponly=True)
    return {"message": "Token refreshed"}


@acc_router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@acc_router.patch("/delete")
def delete_user(response: Response, data: DeleteUserPatch, db: Session = Depends(get_db), user=Depends(get_current_user)):
        
    res = User.delete_user(email=user.email, password=data.password, db=db)
    if res is None:  raise HTTPException(status_code=500, detail="Server Error")
    if res["code"] == 404: raise HTTPException(status_code=401, detail="Incorrect Credentials")
   
    logout(response=response)
    return {"code" : 200, "details": "Account deleted successfully"}



@acc_router.get("/me")
def get_my_details( user = Depends(get_current_user) ):
    
    res = {"username": user.name, "email": user.email, "id": user.id}
    return {"details": res}




@acc_router.patch("/update-profile")
def update_profile(data:UpdateProfilePatch,  user = Depends(get_current_user), db: Session = Depends(get_db)):
    res = User.update_user(old_email= data.oemail, old_name= data.oname, name = data.name, email = data.email, db = db)
    if res is None:
        raise HTTPException(status_code=500, detail="Server Error")
    return {"code": 200, "details": "Success Updating"}



@acc_router.patch("/change-password")
def change_password(data: ChangePasswordPatch, db: Session = Depends(get_db), user=Depends(get_current_user)):
    result = User.change_password(user_id=user.id, old_password=data.old_password, new_password=data.new_password, db=db)
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail="User not found")
    if result["code"] == 401:
        raise HTTPException(status_code=401, detail="Incorrect password")
    if result["code"] == 500:
        raise HTTPException(status_code=500, detail="Server error")
    return {"message": "Password changed successfully"}