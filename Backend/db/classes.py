from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from .database import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    class_code = Column(String, nullable=False, unique=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, onupdate="CASCADE")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())