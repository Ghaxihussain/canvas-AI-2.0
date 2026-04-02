from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, insert, select, update, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
from .users import User
class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    class_code = Column(String, nullable=False, unique=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())



    @classmethod
    def create(cls, name, description, class_code, owner_id, db):
        try:
            if User.get_user_by_id(owner_id, db) is None:
                return None 
            
            if db.execute(select(cls).where(cls.class_code == class_code)).scalar_one_or_none() is not None:
                return False  
            
            db.execute(insert(cls).values(name=name, description=description, class_code=class_code, owner_id=owner_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None
        
    @classmethod
    def get_class_by_id(cls, class_id, db):
        try:
            return db.execute(select(cls).where(cls.id == class_id)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_class_by_code(cls, class_code, db):
        try:
            return db.execute(select(cls).where(cls.class_code == class_code)).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_classes_by_owner(cls, owner_id, db):
        try:
            return db.execute(select(cls).where(cls.owner_id == owner_id)).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def delete_class(cls, class_id, owner_id, db):
        try:
            class_ = cls.get_class_by_id(class_id, db)
            if class_ is None:
                return False  
            if class_.owner_id != owner_id:
                return False  
            db.execute(delete(cls).where(cls.id == class_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None