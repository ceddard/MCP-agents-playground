from sqlalchemy.orm import Session
from src.database.models import Schedule, Finance
from datetime import datetime

# CRUD para Agendamentos
def create_schedule(db: Session, user_id: str, date: datetime, time: str, location: str, description: str):
    schedule = Schedule(user_id=user_id, date=date, time=time, location=location, description=description)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

def get_schedules(db: Session, user_id: str):
    return db.query(Schedule).filter(Schedule.user_id == user_id).all()

def update_schedule(db: Session, schedule_id: int, new_date: datetime, new_time: str, new_location: str, new_description: str):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule:
        schedule.date = new_date
        schedule.time = new_time
        schedule.location = new_location
        schedule.description = new_description
        db.commit()
        db.refresh(schedule)
    return schedule

def delete_schedule(db: Session, schedule_id: int):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule:
        db.delete(schedule)
        db.commit()
    return schedule


# CRUD para Finanças
def create_finance(db: Session, user_id: str, amount: float, description: str, date: datetime, time: str):
    finance = Finance(user_id=user_id, amount=amount, description=description, date=date, time=time)
    db.add(finance)
    db.commit()
    db.refresh(finance)
    return finance

def get_finances(db: Session, user_id: str):
    return db.query(Finance).filter(Finance.user_id == user_id).all()
