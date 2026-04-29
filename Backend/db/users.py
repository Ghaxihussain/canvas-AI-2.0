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
           
            existing = db.execute(select(cls).where(cls.email == email)).scalar_one_or_none()
            
            if existing and not existing.is_deleted:
                return {"code": 400}  
            
            if existing and existing.is_deleted:
                password_hash = cls.hash_password(password)
                db.execute(update(cls).where(cls.email == email).values(
                    name=name,
                    password_hash=password_hash,
                    is_deleted=False
                ))
                db.commit()
                return {"code": 200}
            
            password_hash = cls.hash_password(password)
            db.execute(insert(cls).values(name=name, email=email, password_hash=password_hash))
            db.commit()
            return {"code": 200}
            
        except Exception as e:
            db.rollback()
            print(e)
            return {"code": 500}


    @classmethod
    def get_user_by_email(cls, email, db):
        try:
            return db.execute(select(cls).where(cls.email == email, cls.is_deleted == False)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None
        
    @classmethod
    def get_user_by_name(cls, name, db):
        try:
            return db.execute(select(cls).where(cls.name == name, cls.is_deleted == False)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None
    
    @classmethod
    def get_user_by_id(cls, user_id, db):
        try:
            user =  db.execute(select(cls).where(cls.id == user_id,  cls.is_deleted == False)).scalar_one_or_none()
            if not user:
                return None
            return user
        except Exception as e:
            return {"code": 500}

    @classmethod
    def delete_user(cls, email, password, db):
        try:
            user = db.execute(select(cls).where(cls.email == email)).scalar_one_or_none()
            if user is None: return {"code": 404}
            if not cls.verify_password(password, user.password_hash): return {"code": 404}

            db.execute(update(cls).where(cls.email == email, cls.is_deleted == False).values(is_deleted=True))
            db.commit()
            return {"code": 200}
            
        except Exception as e:
            db.rollback()
            print(e)
            return None
        

    @classmethod
    def verify_user_password(cls, email, password, db):
        try:
            user = cls.get_user_by_email(email=email, db = db)
            if user is not None:
                return str(user.id) if cls.verify_password(password, user.password_hash) else False
        
            else:
                return False
            
        except Exception as e:
            print(e)
            return None
    

        
        
    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    


    @classmethod
    def update_user(cls, old_email:str , email: str, old_name: str, name: str, db):
        try:
            db.execute(update(cls).where(cls.email == old_email, cls.name == old_name, cls.is_deleted == False).values(email = email, name = name))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return None
    

    @classmethod
    def change_password(cls, user_id, old_password, new_password, db):
        try:
            user = cls.get_user_by_id(user_id=user_id, db=db)
            if not user:
                return {"code": 404}
            if not cls.verify_password(old_password, user.password_hash):
                return {"code": 401}
            db.execute(update(cls).where(cls.id == user_id).values(password_hash=cls.hash_password(new_password)))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return {"code": 500}