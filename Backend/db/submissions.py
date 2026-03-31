from sqlalchemy import Column, Text, Integer, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint
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