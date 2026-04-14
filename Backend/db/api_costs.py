import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, insert
from Backend.db.database import Base  # adjust to your Base import

class APICost(Base):
    __tablename__ = "api_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    model = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)          
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cached_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    model_costs = {
    "gpt-4o":               {"input": 2.50,  "cached": 1.25,  "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,  "cached": 0.075, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02, "output": 0.00},
    "text-embedding-3-large": {"input": 0.13, "output": 0.00},}

    @classmethod
    def create(cls, user_id, model, endpoint, input_tokens, output_tokens, cost, db, cached_tokens=0):
        try:
            db.execute(insert(cls).values(
                user_id=user_id,
                model=model,
                endpoint=endpoint,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                estimated_cost_usd= cost
            ))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None
        

    @classmethod
    def calculate_cost(cls, input_tokens, output_tokens, model, cached_tokens=0):
        pricing = cls.model_costs.get(model)
        if not pricing:
            return 0.0
        non_cached = input_tokens - cached_tokens
        input_cost  = (non_cached     / 1_000_000) * pricing["input"]
        cache_cost  = (cached_tokens  / 1_000_000) * pricing.get("cached", pricing["input"] * 0.5)
        output_cost = (output_tokens  / 1_000_000) * pricing["output"]
        return round(input_cost + cache_cost + output_cost, 8)