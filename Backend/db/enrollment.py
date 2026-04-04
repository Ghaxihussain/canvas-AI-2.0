from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, UniqueConstraint, CheckConstraint, insert, select, update, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("class_id", "user_id", name="uq_enrollment_class_user"),
        CheckConstraint("role IN ('teacher', 'student')", name="ck_enrollment_role"),
    )

    @classmethod
    def create(cls, class_id, user_id, role, db):
        try:
            if role not in ['teacher', 'student']:
                return False  

            existing = db.execute(
                select(cls).where(cls.class_id == class_id, cls.user_id == user_id)
            ).scalar_one_or_none()

            if existing is not None:
                return False 

            db.execute(insert(cls).values(class_id=class_id, user_id=user_id, role=role))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete(cls, class_id, user_id, db):
        try:
            existing = db.execute(
                select(cls).where(cls.class_id == class_id, cls.user_id == user_id)
            ).scalar_one_or_none()

            if existing is None:
                return False  

            db.execute(delete(cls).where(cls.class_id == class_id, cls.user_id == user_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def update_role(cls, class_id, user_id, new_role, db):
        try:
            if new_role not in ['teacher', 'student']:
                return False  # invalid role

            existing = db.execute(
                select(cls).where(cls.class_id == class_id, cls.user_id == user_id)
            ).scalar_one_or_none()

            if existing is None:
                return False  

            db.execute(
                update(cls)
                .where(cls.class_id == class_id, cls.user_id == user_id)
                .values(role=new_role)
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None
        
    

    @classmethod
    def get_user_enrollments(cls, user_id, db):
        try:
            return [
                {"class_id": i.class_id, 
                "user_id": i.user_id, 
                "role": i.role, 
                "created_at": i.created_at} 
                for i in db.execute(select(cls).where(cls.user_id == user_id)).scalars().all()
                    ]
        except Exception as e:
            print(e)
            return None