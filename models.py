from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id                       = Column(Integer, primary_key=True, index=True)
    username                 = Column(String, unique=True, nullable=False)
    password_hash            = Column(String, nullable=False)
    name                     = Column(String, default="")
    dietary                  = Column(String, default="non-vegetarian")
    cuisine_preferences      = Column(String, default='["Indian"]')  # JSON string
    allergies                = Column(String, default="[]")           # JSON string
    max_cook_time_busy_day   = Column(Integer, default=30)
    max_cook_time_normal_day = Column(Integer, default=55)
    work_hours               = Column(String, default="9am-6pm")
    peak_energy_hours        = Column(String, default="9am-12pm")
    family_size              = Column(Integer, default=1)
    height_cm                = Column(Integer, default=160)
    weight_kg                = Column(Integer, default=60)
    age                      = Column(Integer, default=30)
    created_at               = Column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, default=1)
    title      = Column(String, nullable=False)
    domain     = Column(String, nullable=False)   # "work" or "home"
    priority   = Column(String, default="medium") # "high", "medium", "low"
    category   = Column(String, default="")
    due_date   = Column(String, default="")
    est_mins   = Column(Integer, default=30)
    done       = Column(Boolean, default=False)
    deferred   = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, default=1)
    log_date        = Column(String, nullable=False)
    tasks_done      = Column(Integer, default=0)
    meals_planned   = Column(Integer, default=0)
    time_saved_mins = Column(Integer, default=0)
    energy_level    = Column(String, default="medium")
    created_at      = Column(DateTime, server_default=func.now())


class Meal(Base):
    __tablename__ = "meals"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, default=1)
    meal_type      = Column(String, default="dinner")
    name           = Column(String, nullable=False)
    prep_time_mins = Column(Integer, default=0)
    instructions   = Column(String, default="")
    ingredients    = Column(String, default="")   # JSON string list
    reuse_tip      = Column(String, default="")
    status         = Column(String, default="suggested")  # "suggested", "accepted", "rejected"
    suggested_on   = Column(DateTime, server_default=func.now())
