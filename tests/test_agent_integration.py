import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.agents.finance_agent import finance_agent_executor
from src.agents.scheduling_agent import scheduling_agent_executor
from src.database.crud import get_finances, get_schedules

# Usar um banco de dados de teste separado para integração
DATABASE_URL = "postgresql://user:password@localhost:5432/test_your_database"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    """Cria e derruba o banco de dados de teste uma vez por módulo."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_database):
    """Fornece uma sessão de banco de dados limpa para cada teste."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Limpa as tabelas após cada teste para garantir isolamento
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()

# --- Testes do Agente Financeiro ---

def test_finance_agent_add_transaction_and_get_balance(db_session):
    # 1. Adicionar uma transação de entrada
    input_data_add = {
        "input": json.dumps({
            "user_id": "user123",
            "amount": 1500.75,
            "description": "Salário"
        })
    }
    # O agente espera uma string, não um dict
    result_add = finance_agent_executor.invoke({"input": f"Adicionar transação: {input_data_add['input']}"})
    
    assert "Transação de R$ 1500.75 adicionada" in result_add['output']
    
    # Verificar no banco de dados diretamente
    finances = get_finances(db_session, user_id="user123")
    assert len(finances) == 1
    assert finances[0].amount == 1500.75

    # 2. Adicionar uma transação de saída
    input_data_expense = {
        "input": json.dumps({
            "user_id": "user123",
            "amount": -250.50,
            "description": "Compras"
        })
    }
    finance_agent_executor.invoke({"input": f"Adicionar transação: {input_data_expense['input']}"})

    # 3. Consultar o saldo
    input_data_balance = {"input": json.dumps({"user_id": "user123"})}
    result_balance = finance_agent_executor.invoke({"input": f"Qual meu saldo? {input_data_balance['input']}"})

    assert "O saldo atual para o usuário user123 é de R$ 1250.25" in result_balance['output']


# --- Testes do Agente de Agendamento ---

def test_scheduling_agent_add_list_and_remove_schedule(db_session):
    # 1. Adicionar um agendamento
    input_add = {
        "input": json.dumps({
            "user_id": "user456",
            "date": "2025-10-20",
            "time": "10:00",
            "location": "Sala de Reuniões 5",
            "description": "Reunião de planejamento trimestral"
        })
    }
    result_add = scheduling_agent_executor.invoke({"input": f"Criar agendamento: {input_add['input']}"})
    
    assert "Agendamento criado com sucesso com o ID:" in result_add['output']
    
    # Extrair o ID do resultado
    schedule_id_str = result_add['output'].split(":")[-1].strip()
    schedule_id = int(schedule_id_str)

    # Verificar no banco de dados
    schedules = get_schedules(db_session, user_id="user456")
    assert len(schedules) == 1
    assert schedules[0].description == "Reunião de planejamento trimestral"

    # 2. Listar agendamentos
    input_list = {"input": json.dumps({"user_id": "user456"})}
    result_list = scheduling_agent_executor.invoke({"input": f"Listar meus agendamentos: {input_list['input']}"})
    
    assert "Reunião de planejamento trimestral" in result_list['output']
    assert "2025-10-20" in result_list['output']

    # 3. Remover o agendamento
    input_remove = {"input": json.dumps({"schedule_id": schedule_id})}
    result_remove = scheduling_agent_executor.invoke({"input": f"Remover o agendamento: {input_remove['input']}"})

    assert f"Agendamento {schedule_id} removido com sucesso" in result_remove['output']

    # Verificar no banco de dados
    schedules_after_delete = get_schedules(db_session, user_id="user456")
    assert len(schedules_after_delete) == 0
