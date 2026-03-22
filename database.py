from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite file stored in the project folder
DATABASE_URL = "sqlite:///./women_ai.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import User, Task, Meal, DailyLog  # noqa: F401 — ensures all tables are registered
    Base.metadata.create_all(bind=engine)
