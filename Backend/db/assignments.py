from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey, insert, select, update, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    text_content = Column(Text)
    rubric_text_content = Column(Text)
    assignment_file_url = Column(Text)
    rubric_file_url = Column(Text)
    total_grade = Column(Integer, nullable=False, default=100)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    @classmethod
    def create(cls, class_id, created_by, title, db, text_content=None, rubric_text_content=None,
               assignment_file_url=None, rubric_file_url=None, total_grade=100):
        try:
            db.execute(insert(cls).values(
                class_id=class_id,
                created_by=created_by,
                title=title,
                text_content=text_content,
                rubric_text_content=rubric_text_content,
                assignment_file_url=assignment_file_url,
                rubric_file_url=rubric_file_url,
                total_grade=total_grade
            ))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def get_assignment_by_id(cls, assignment_id, db):
        try:
            return db.execute(
                select(cls).where(cls.id == assignment_id)
            ).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_assignments_by_class_id(cls, class_id, db):
        try:
            return db.execute(
                select(cls).where(cls.class_id == class_id)
            ).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def update_assignment(cls, assignment_id, db, title=None, text_content=None, rubric_text_content=None,
                          assignment_file_url=None, rubric_file_url=None, total_grade=None):
        try:
            assignment = cls.get_assignment_by_id(assignment_id, db)
            if assignment is None:
                return False

            new_values = {k: v for k, v in {
                "title": title,
                "text_content": text_content,
                "rubric_text_content": rubric_text_content,
                "assignment_file_url": assignment_file_url,
                "rubric_file_url": rubric_file_url,
                "total_grade": total_grade
            }.items() if v is not None}

            db.execute(update(cls).where(cls.id == assignment_id).values(**new_values))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete_assignment(cls, assignment_id, db):
        try:
            assignment = cls.get_assignment_by_id(assignment_id, db)
            if assignment is None:
                return False

            db.execute(delete(cls).where(cls.id == assignment_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

