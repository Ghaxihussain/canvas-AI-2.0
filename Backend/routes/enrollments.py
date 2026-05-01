import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Backend.db.database import get_db
from Backend.routes.helpers import get_current_user
from datetime import datetime
from Backend.db.enrollment import Enrollment





enroll_router = APIRouter(prefix= "/enrollment")



@enroll_router.post("/enroll-student/{class_code}")
def enroll_student(class_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Enrollment.create(class_code=class_code, user_id=user.id, role="student", db=db)
    if res is None: raise HTTPException(status_code=500, detail="Server Error")
    if res["code"] == 404: raise HTTPException(status_code=404, detail="Class not found")
    if res["code"] == 409: raise HTTPException(status_code=409, detail="Already enrolled")
    return {"code": 200, "detail": "Enrolled successfully"}



@enroll_router.post("/enroll-teacher/{class_code}")
def enroll_teacher(class_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Enrollment.create(class_code=class_code, user_id=user.id, role="teacher", db=db)
    if res is None: raise HTTPException(status_code=500, detail="Server Error")
    if res["code"] == 404: raise HTTPException(status_code=404, detail="Class not found")
    if res["code"] == 409: raise HTTPException(status_code=409, detail="Already enrolled")
    return {"code": 200, "detail": "Enrolled successfully"}



@enroll_router.delete("/unenroll/{class_code}")
def unenroll(class_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Enrollment.delete(class_code=class_code, user_id=user.id, db=db)
    if res is None: raise HTTPException(status_code=500, detail="Server Error")
    if res["code"] == 404: raise HTTPException(status_code=404, detail="Class or enrollment not found")
    return {"code": 200, "detail": "Unenrolled successfully"}





