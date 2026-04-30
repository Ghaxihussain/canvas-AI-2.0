import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Backend.db.database import get_db
from Backend.routes.helpers import get_current_user

from Backend.db.announcement import Announcement

ann_router = APIRouter(prefix="/announcements", tags = ["Announcement"])


class CreateAnnouncementPost(BaseModel):
    title: str
    content: str

class UpdateAnnouncement(BaseModel):
    title: str
    content: str

@ann_router.post("/{class_code}")
def create_announcement(data: CreateAnnouncementPost, class_code: str, user= Depends(get_current_user), db: Session = Depends(get_db)):
    res = Announcement.create(class_code= class_code, author_id= user.id, title = data.title, content= data.content, db = db)
    if res is None: raise HTTPException(status_code=500, detail= "Sereve Error") 
    if res["code"] == 404: raise HTTPException(status_code=404, detail= "Class not found")
    return {"code": 200, "detail": "Announcement Created"}  



@ann_router.get("/{class_code}")
def get_class_announcements(class_code: str, user= Depends(get_current_user), db: Session = Depends(get_db)):
    res = Announcement.get_class_announcements(code = class_code, db =db)
    if res is None: raise HTTPException(status_code=500, detail= "Sereve Error") 
    if res["code"] == 404: raise HTTPException(status_code=404, detail= "Class not found")
    return res




@ann_router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Announcement.delete_announcement(announcement_id=announcement_id, author_id=user.id, db=db)
    if res is None: raise HTTPException(status_code=500, detail="Server Error")
    if res["code"] == 404: raise HTTPException(status_code=404, detail="Announcement not found")
    if res["code"] == 403: raise HTTPException(status_code=403, detail="Not authorized")
    return {"code": 200, "detail": "Announcement deleted"}