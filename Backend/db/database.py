from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase



DATABASE_URL =  "postgresql+psycopg2://myuser:123@localhost:5432/canvas_ai"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db():
    Base.metadata.create_all(engine)
