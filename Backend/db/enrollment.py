from sqlalchemy import Column, String,text, TIMESTAMP, ForeignKey, UniqueConstraint, CheckConstraint, insert, select, update, delete, join
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base
from .users import User


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

    classmethod
    def create(cls, class_code, user_id, role, db):
        try:
            class_ = db.execute(text("SELECT id FROM classes WHERE class_code = :code"), {"code": class_code}).mappings().one_or_none()

            if class_ is None:
                return {"code": 404}

            existing = db.execute(select(cls).where(cls.class_id == class_["id"], cls.user_id == user_id)).scalar_one_or_none()

            if existing is not None:
                return {"code": 409}

            db.execute(insert(cls).values(class_id=class_["id"], user_id=user_id, role=role))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete(cls, class_code, user_id, db):
        try:
            class_ = db.execute(
                text("SELECT id FROM classes WHERE class_code = :code"), {"code": class_code}
            ).mappings().one_or_none()

            if class_ is None:
                return {"code": 404}

            existing = db.execute(
                select(cls).where(cls.class_id == class_["id"], cls.user_id == user_id)
            ).scalar_one_or_none()

            if existing is None:
                return {"code": 404}

            db.execute(delete(cls).where(cls.class_id == class_["id"], cls.user_id == user_id))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return None
        
        
    @classmethod
    def update_role(cls, class_id, user_id, new_role, db):
        try:
            if new_role not in ['teacher', 'student']:
                return False  

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
        

    @classmethod
    def get_class_enrollments(cls, class_id, db):
        try:
            res = db.execute(
                select(cls, User.name, User.email, User.id)
                .select_from(cls)
                .join(User, cls.user_id == User.id)
                .where(cls.class_id == class_id)
            ).all()

            return [
                {
                    "user_id": str(row[0].user_id),
                    "name": row[1],
                    "email": row[2],
                    "role": row[0].role,
                    "created_at": row[0].created_at,
                }
                for row in res
            ]
        except Exception as e:
           return {"status_code": 404, "content": f"error {e}", "return": None}

    

@classmethod
def unenroll_person(cls, id, class_code, db):
    try:
        class_ = db.execute(
            text("SELECT id FROM classes WHERE class_code = :code"), {"code": class_code}).mappings().one_or_none()

        if class_ is None:
            return {"code": 404}

        existing = db.execute(
            select(cls).where(cls.id == id, cls.class_id == class_["id"])).scalar_one_or_none()

        if existing is None:
            return {"code": 404}

        db.execute(delete(cls).where(cls.id == id, cls.class_id == class_["id"]))
        db.commit()
        return {"code": 200}
    except Exception as e:
        db.rollback()
        print(e)
        return None