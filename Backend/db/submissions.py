from sqlalchemy import Column, Text, Integer, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint, insert, select, update, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text_content = Column(Text)
    file_url = Column(Text)
    graded = Column(Boolean, default=False)
    grade = Column(Integer)
    feedback = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("assignment_id", "user_id", name="uq_submission_assignment_user"),
    )

    @classmethod
    def create(cls, assignment_id, user_id, db, text_content=None, file_url=None):
        try:
            existing = db.execute(
                select(cls).where(cls.assignment_id == assignment_id, cls.user_id == user_id)
            ).scalar_one_or_none()

            if existing is not None:
                return False 

            db.execute(insert(cls).values(
                assignment_id=assignment_id,
                user_id=user_id,
                text_content=text_content,
                file_url=file_url
            ))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def get_submission_by_id(cls, submission_id, db):
        try:
            return db.execute(
                select(cls).where(cls.id == submission_id)
            ).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_submission_by_assignment_and_user(cls, assignment_id, user_id, db):
        try:
            return db.execute(
                select(cls).where(cls.assignment_id == assignment_id, cls.user_id == user_id)
            ).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_submissions_by_assignment(cls, assignment_id, db):
        try:
            return db.execute(
                select(cls).where(cls.assignment_id == assignment_id)
            ).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_submissions_by_user(cls, user_id, db):
        try:
            return db.execute(
                select(cls).where(cls.user_id == user_id)
            ).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def update_submission(cls, assignment_id, user_id, db, text_content=None, file_url=None):
        try:
            existing = cls.get_submission_by_assignment_and_user(assignment_id, user_id, db)
            if existing is None:
                return False

            new_values = {k: v for k, v in {
                "text_content": text_content,
                "file_url": file_url
            }.items() if v is not None}

            db.execute(
                update(cls)
                .where(cls.assignment_id == assignment_id, cls.user_id == user_id)
                .values(**new_values)
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def grade_submission(cls, assignment_id, user_id, grade, db, feedback=None):
        try:
            existing = cls.get_submission_by_assignment_and_user(assignment_id, user_id, db)
            if existing is None:
                return False

            new_values = {"graded": True, "grade": grade}
            if feedback is not None:
                new_values["feedback"] = feedback

            db.execute(
                update(cls)
                .where(cls.assignment_id == assignment_id, cls.user_id == user_id)
                .values(**new_values)
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete_submission(cls, assignment_id, user_id, db):
        try:
            existing = cls.get_submission_by_assignment_and_user(assignment_id, user_id, db)
            if existing is None:
                return False

            db.execute(
                delete(cls).where(cls.assignment_id == assignment_id, cls.user_id == user_id)
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None