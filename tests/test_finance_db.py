import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Finance
from src.database.crud import create_finance, get_finances
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

def test_create_and_get_finance(db_session):
    now = datetime.now()
    # Adicionar uma transação
    create_finance(db_session, user_id="test_user", amount=100.50, description="Depósito", date=now, time=now.strftime("%H:%M:%S"))
    
    # Adicionar outra transação
    create_finance(db_session, user_id="test_user", amount=-25.00, description="Café", date=now, time=now.strftime("%H:%M:%S"))

    # Verificar o saldo
    finances = get_finances(db_session, user_id="test_user")
    assert len(finances) == 2
    balance = sum(f.amount for f in finances if f.amount is not None)
    assert balance == 75.50

    # Verificar outra pessoa
    finances_other = get_finances(db_session, user_id="other_user")
    assert len(finances_other) == 0
