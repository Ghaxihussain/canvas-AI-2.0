from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey,text, insert, select, update, delete
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
    def create(cls, class_code, author_id, title, content, db):
        try:
            res = db.execute(text("SELECT * FROM classes WHERE class_code = :code"), {"code": class_code}).mappings().one_or_none()
            if res is None:
                return {"code": 404}
            
            db.execute(insert(cls).values(
                class_id=res["id"],
                author_id=author_id,
                title=title,
                content=content
            ))
            db.commit()
            return {"code": 200}
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
    def update_announcement(cls, announcement_id, author_id, db, title=None, content=None):
        try:
            announcement = cls.get_announcement_by_id(announcement_id, db)
            if announcement is None:
                return {"code": 404}
            
            if announcement.author_id != author_id:
                return {"code": 403}

            new_values = {k: v for k, v in {
                "title": title,
                "content": content
            }.items() if v is not None}

            if not new_values:
                return {"code": 400}  

            db.execute(update(cls).where(cls.id == announcement_id).values(**new_values))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete_announcement(cls, announcement_id, author_id, db):
        try:
            announcement = cls.get_announcement_by_id(announcement_id, db)
            if announcement is None:
                return {"code": 404}
            
            if announcement.author_id != author_id:
                return {"code": 403}

            db.execute(delete(cls).where(cls.id == announcement_id))
            db.commit()
            return {"code": 200}
        except Exception as e:
            db.rollback()
            print(e)
            return None
            
    @classmethod
    def get_class_announcements(cls, code, db):
        try: 
            res = db.execute(text("SELECT id FROM classes WHERE class_code = :code"), {"code": code}).mappings().one_or_none()
            if res is None:
                return {"code": 404}
            
            announcements = db.execute(select(cls).where(cls.class_id == res["id"])).scalars().all()
            return {"code": 200, "data": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "content": a.content,
                    "created_at": str(a.created_at)
                } for a in announcements
            ]}
        except Exception as e:
            print(e)
            return None