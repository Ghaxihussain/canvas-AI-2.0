from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, insert, select, update, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    @classmethod
    def create(cls, class_id, author_id, title, content, db):
        try:
            db.execute(insert(cls).values(
                class_id=class_id,
                author_id=author_id,
                title=title,
                content=content
            ))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def get_announcement_by_id(cls, announcement_id, db):
        try:
            return db.execute(
                select(cls).where(cls.id == announcement_id)
            ).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_announcements_by_class_id(cls, class_id, db):
        try:
            return db.execute(
                select(cls).where(cls.class_id == class_id).order_by(cls.created_at.desc())
            ).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def update_announcement(cls, announcement_id, db, title=None, content=None):
        try:
            announcement = cls.get_announcement_by_id(announcement_id, db)
            if announcement is None:
                return False

            new_values = {k: v for k, v in {
                "title": title,
                "content": content
            }.items() if v is not None}

            db.execute(update(cls).where(cls.id == announcement_id).values(**new_values))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete_announcement(cls, announcement_id, db):
        try:
            announcement = cls.get_announcement_by_id(announcement_id, db)
            if announcement is None:
                return False

            db.execute(delete(cls).where(cls.id == announcement_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None