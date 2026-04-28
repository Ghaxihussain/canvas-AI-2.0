from sqlalchemy import Column, String, Text, TIMESTAMP, insert, select, delete, Boolean, update
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
import bcrypt



class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    @classmethod
    def create(cls, name, email, password, db):
        try:
            if cls.get_user_by_email(email= email, db = db):
                return {"code": 400}
            password_hash = cls.hash_password(password)
            db.execute(insert(cls).values(name=name, email=email, password_hash=password_hash))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()  
            print(e)       
            return {"code": 404}
        


    @classmethod
    def get_user_by_email(cls, email, db):
        try:
            return db.execute(select(cls).where(cls.email == email)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None
        
    @classmethod
    def get_user_by_name(cls, name, db):
        try:
            return db.execute(select(cls).where(cls.name == name)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None
    
    @classmethod
    def get_user_by_id(cls, user_id, db):
        try:
            return db.execute(select(cls).where(cls.id == user_id)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def delete_user(cls, email, password, db):
        try:
            if cls.verify_user_password(email=email, password=password, db=db):
                db.execute(update(cls).where(cls.email == email).values(is_deleted=True))
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(e)
            return None
        

    @classmethod
    def verify_user_password(cls, email, password, db):
        try:
            user = cls.get_user_by_email(email=email, db = db)
            if user is not None:
                return {"code": 200, "user_id": str(user.id)} if cls.verify_password(password, user.password_hash) else {"code": 401}
            
        
            else:
                return {"code": 404}
            
        except Exception as e:
            print(e)
            return None
    

        
        
    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))