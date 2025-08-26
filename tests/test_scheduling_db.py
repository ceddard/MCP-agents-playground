import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Schedule
from src.database.crud import create_schedule, get_schedules, update_schedule, delete_schedule
from datetime import datetime

# Setup do banco de dados em memória para testes
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")

def test_create_and_get_schedule(db_session):
    # Adicionar um agendamento
    schedule = create_schedule(db_session, user_id="test_user", date=_parse_date("2025-09-10"), time="14:00", location="Online", description="Reunião de Projeto")
    assert schedule.id is not None
    assert schedule.description == "Reunião de Projeto"

    # Listar agendamentos
    schedules = get_schedules(db_session, user_id="test_user")
    assert len(schedules) == 1
    assert schedules[0].location == "Online"

def test_update_schedule(db_session):
    # Criar agendamento inicial
    schedule = create_schedule(db_session, user_id="test_user", date=_parse_date("2025-09-10"), time="14:00", location="Online", description="Reunião de Projeto")
    
    # Atualizar
    schedule_id = schedule.id
    assert schedule_id is not None
    updated_schedule = update_schedule(db_session, schedule_id=schedule_id, new_date=_parse_date("2025-09-11"), new_time="15:30", new_location="Escritório", new_description="Reunião de Alinhamento")
    assert updated_schedule is not None
    assert updated_schedule.location == "Escritório"
    assert updated_schedule.time == "15:30"

    # Verificar se a atualização persistiu
    schedules = get_schedules(db_session, user_id="test_user")
    assert schedules[0].location == "Escritório"

def test_delete_schedule(db_session):
    # Criar e deletar
    schedule = create_schedule(db_session, user_id="test_user", date=_parse_date("2025-09-10"), time="14:00", location="Online", description="Reunião de Projeto")
    schedule_id = schedule.id
    assert schedule_id is not None
    delete_schedule(db_session, schedule_id=schedule_id)

    # Verificar se foi deletado
    schedules = get_schedules(db_session, user_id="test_user")
    assert len(schedules) == 0
