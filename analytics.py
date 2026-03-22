from datetime import date, timedelta
from sqlalchemy.orm import Session
from models import DailyLog, Task, Meal


def log_daily_plan(db: Session, time_saved_mins: int, energy_level: str, meals_planned: int = 3):
    """Called every time the user generates a daily plan."""
    today = str(date.today())
    existing = db.query(DailyLog).filter(DailyLog.log_date == today).first()
    if existing:
        existing.time_saved_mins = time_saved_mins
        existing.meals_planned   = meals_planned
        existing.energy_level    = energy_level
    else:
        log = DailyLog(
            log_date=today,
            time_saved_mins=time_saved_mins,
            meals_planned=meals_planned,
            energy_level=energy_level
        )
        db.add(log)
    db.commit()


def get_weekly_summary(db: Session) -> dict:
    """Returns last 7 days of logs for the analytics dashboard."""
    today = date.today()
    days  = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    labels      = [d.strftime("%a %d") for d in days]
    time_saved  = []
    meals_count = []
    energy_list = []

    for d in days:
        log = db.query(DailyLog).filter(DailyLog.log_date == str(d)).first()
        time_saved.append(log.time_saved_mins if log else 0)
        meals_count.append(log.meals_planned if log else 0)
        energy_list.append(log.energy_level if log else "—")

    total_time_saved  = sum(time_saved)
    total_meals       = sum(meals_count)
    tasks_done        = db.query(Task).filter(Task.done == True).count()
    meals_accepted    = db.query(Meal).filter(Meal.status == "accepted").count()
    meals_rejected    = db.query(Meal).filter(Meal.status == "rejected").count()

    return {
        "labels":           labels,
        "time_saved":       time_saved,
        "meals_count":      meals_count,
        "energy_list":      energy_list,
        "total_time_saved": total_time_saved,
        "total_meals":      total_meals,
        "tasks_done":       tasks_done,
        "meals_accepted":   meals_accepted,
        "meals_rejected":   meals_rejected,
    }
