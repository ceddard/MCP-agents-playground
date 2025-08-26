from langchain.agents import Tool
from src.database.crud import create_schedule, get_schedules, update_schedule, delete_schedule
from src.database.session import get_db
from datetime import datetime
import json

def _parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")

def add_schedule(user_id: str, date: str, time: str, location: str, description: str) -> str:
    """Use this tool to add a new schedule."""
    db = next(get_db())
    parsed_date = _parse_date(date)
    schedule = create_schedule(db, user_id=user_id, date=parsed_date, time=time, location=location, description=description)
    return f"Agendamento criado com sucesso com o ID: {schedule.id}"

def list_schedules(user_id: str) -> str:
    """Use this tool to list all schedules for a user."""
    db = next(get_db())
    schedules = get_schedules(db, user_id=user_id)
    if not schedules:
        return f"Nenhum agendamento encontrado para o usuário {user_id}."
    
    return json.dumps([
        {
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "time": s.time,
            "location": s.location,
            "description": s.description,
        }
        for s in schedules
    ], indent=2)

def modify_schedule(schedule_id: int, new_date: str, new_time: str, new_location: str, new_description: str) -> str:
    """Use this tool to modify an existing schedule."""
    db = next(get_db())
    parsed_date = _parse_date(new_date)
    schedule = update_schedule(db, schedule_id=schedule_id, new_date=parsed_date, new_time=new_time, new_location=new_location, new_description=new_description)
    if schedule:
        return f"Agendamento {schedule_id} atualizado com sucesso."
    return f"Agendamento com ID {schedule_id} não encontrado."

def remove_schedule(schedule_id: int) -> str:
    """Use this tool to remove a schedule by its ID."""
    db = next(get_db())
    schedule = delete_schedule(db, schedule_id=schedule_id)
    if schedule:
        return f"Agendamento {schedule_id} removido com sucesso."
    return f"Agendamento com ID {schedule_id} não encontrado."

scheduling_tools = [
    Tool(
        name="add_schedule",
        func=lambda query: add_schedule(**json.loads(query)),
        description="Adiciona um novo agendamento. Requer 'user_id', 'date' (YYYY-MM-DD), 'time', 'location', 'description'.",
    ),
    Tool(
        name="list_schedules",
        func=lambda query: list_schedules(json.loads(query)["user_id"]),
        description="Lista todos os agendamentos de um usuário. Requer 'user_id'.",
    ),
    Tool(
        name="modify_schedule",
        func=lambda query: modify_schedule(**json.loads(query)),
        description="Modifica um agendamento existente. Requer 'schedule_id', 'new_date', 'new_time', 'new_location', 'new_description'.",
    ),
    Tool(
        name="remove_schedule",
        func=lambda query: remove_schedule(json.loads(query)["schedule_id"]),
        description="Remove um agendamento pelo seu ID. Requer 'schedule_id'.",
    ),
]
