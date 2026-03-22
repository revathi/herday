import hashlib
import json
from sqlalchemy.orm import Session
from models import User, Task, Meal


# ── Auth ──────────────────────────────────────────────────────────────────────

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(db: Session, username: str, password: str, name: str, **profile) -> User:
    user = User(username=username, password_hash=_hash_pw(password), name=name, **profile)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def verify_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if user and user.password_hash == _hash_pw(password):
        return user
    return None

def update_user_profile(db: Session, user_id: int, **fields) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    for k, v in fields.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user

def seed_demo_user(db: Session):
    if not get_user_by_username(db, "revathi"):
        create_user(db, username="revathi", password="demo123", name="Revathi",
                    dietary="non-vegetarian",
                    cuisine_preferences='["Indian"]',
                    allergies="[]",
                    max_cook_time_busy_day=30,
                    max_cook_time_normal_day=55,
                    family_size=3,
                    height_cm=161,
                    weight_kg=70,
                    age=40)


# ── Task CRUD ─────────────────────────────────────────────────────────────────

def add_task(db: Session, user_id: int, title: str, domain: str, priority: str = "medium",
             category: str = "", due_date: str = "", est_mins: int = 30) -> Task:
    task = Task(user_id=user_id, title=title, domain=domain, priority=priority,
                category=category, due_date=due_date, est_mins=est_mins)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks(db: Session, user_id: int, domain: str = None, done: bool = False, deferred: bool = False):
    query = db.query(Task).filter(Task.user_id == user_id, Task.done == done, Task.deferred == deferred)
    if domain:
        query = query.filter(Task.domain == domain)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(query.all(), key=lambda t: priority_order.get(t.priority, 1))

def mark_done(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.done = True
        db.commit()
        db.refresh(task)
    return task

def defer_task(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.deferred = True
        db.commit()
        db.refresh(task)
    return task

def restore_task(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.deferred = False
        db.commit()
        db.refresh(task)
    return task

def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()

def seed_tasks(db: Session, user_id: int):
    if db.query(Task).filter(Task.user_id == user_id).count() == 0:
        default_tasks = [
            {"title": "Finish Q1 report",       "domain": "work", "priority": "high",   "due_date": "today",      "est_mins": 90},
            {"title": "Reply to client emails",  "domain": "work", "priority": "medium", "due_date": "today",      "est_mins": 30},
            {"title": "Review design mockups",   "domain": "work", "priority": "low",    "due_date": "this week",  "est_mins": 45},
            {"title": "Grocery shopping",        "domain": "home", "priority": "high",   "category": "Errands",    "est_mins": 45},
            {"title": "Do laundry",              "domain": "home", "priority": "medium", "category": "Cleaning",   "est_mins": 60},
            {"title": "Call mom",                "domain": "home", "priority": "low",    "category": "Personal",   "est_mins": 20},
        ]
        for t in default_tasks:
            add_task(db, user_id=user_id, **t)


# ── Meal CRUD ─────────────────────────────────────────────────────────────────

def save_meal(db: Session, user_id: int, name: str, prep_time_mins: int,
              instructions: str, ingredients: list,
              meal_type: str = "dinner", reuse_tip: str = "") -> Meal:
    meal = Meal(user_id=user_id, meal_type=meal_type, name=name,
                prep_time_mins=prep_time_mins, instructions=instructions,
                ingredients=json.dumps(ingredients), reuse_tip=reuse_tip)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal

def get_meals(db: Session, user_id: int, status: str = None):
    query = db.query(Meal).filter(Meal.user_id == user_id)
    if status:
        query = query.filter(Meal.status == status)
    return query.order_by(Meal.suggested_on.desc()).all()

def update_meal_status(db: Session, meal_id: int, status: str) -> Meal:
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if meal:
        meal.status = status
        db.commit()
        db.refresh(meal)
    return meal

def get_rejected_meal_names(db: Session, user_id: int) -> list:
    rejected = db.query(Meal).filter(Meal.user_id == user_id, Meal.status == "rejected").all()
    return [m.name for m in rejected]
