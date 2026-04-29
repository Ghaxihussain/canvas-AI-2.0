import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Backend.db.classes import Class
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Backend.db.database import get_db
from pydantic import BaseModel
from Backend.routes.helpers import get_current_user

class_router = APIRouter(prefix="/classes", tags = ["Class"])


class CreatePost(BaseModel):
    name: str
    description: str
    class_code: str
    
class UpdateClassPatch(BaseModel):
    name: str | None = None
    description: str | None = None



@class_router.post("/create")
def create_class(data: CreatePost,  user = Depends(get_current_user), db : Session = Depends(get_db)):
    res = Class.create(name = data.name,  class_code = data.class_code, description = data.description, owner_id=user.id, db = db)
    if res is None: raise HTTPException(status_code=500, detail= "Server Error")
    if res["code"] == 404: raise HTTPException(status_code=404, detail= "User Not found")
    if res["code"] == 400:  raise HTTPException(status_code=400, detail= "Class Code Already exists, Class not created")
    if res["code"] == 200: return {"code": 200, "details": "Succes creating class"}


@class_router.get("/me")
def get_my_classes(user = Depends(get_current_user), db : Session = Depends(get_db)):
    res = Class.get_classes_by_owner(owner_id= user.id, db = db)
    if res is None: raise HTTPException(status_code=500, detail= "Server Error")
    return {"code": 200, "details": [{"name": classes.name, "class_code": classes.class_code, "desc": classes.description, "created_at": classes.created_at} for classes in res]}


@class_router.get("/{class_code}")
def get_class_by_code(class_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Class.get_class_by_code(class_code=class_code, db=db)
    if res["code"] is None: raise HTTPException(status_code=500, detail="Server error")
    if res["code"] == 404:
        raise HTTPException(status_code=404, detail="Class not found")
    
    c = res["class"]
    return {"name": c.name, "class_code": c.class_code, "desc": c.description, "created_at": c.created_at}




@class_router.delete("/{class_code}")
def delete_class(class_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    res = Class.get_class_by_code(class_code=class_code, db=db)
    if res["code"] == 404:
        raise HTTPException(status_code=404, detail="Class not found")
    if res["code"] == 500:
        raise HTTPException(status_code=500, detail="Server error")
    
    if res["class"].owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your class")
    
    result = Class.delete_class(class_id=res["class"].id, db=db)
    if result is None:
        raise HTTPException(status_code=500, detail="Server error")
    return {"code": 200, "detail": "Class deleted successfully"}