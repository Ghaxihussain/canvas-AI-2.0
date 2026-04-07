import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.users import User




TEST_DATABASE_URL = "postgresql+psycopg2://myuser:123@localhost:5432/canvas_ai_test"


engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(engine)  
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)  