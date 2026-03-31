from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, UniqueConstraint, CheckConstraint
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