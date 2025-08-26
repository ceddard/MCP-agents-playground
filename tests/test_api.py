import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Carrega o arquivo .env para garantir que as variáveis de ambiente estejam disponíveis
load_dotenv()

# Adiciona o diretório raiz ao path para que o `main` possa importar de `src`
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

@pytest.fixture
def mock_orchestrator():
    """Mock para o agent_orchestrator para evitar chamadas reais à API."""
    with patch('main.agent_orchestrator') as mock:
        yield mock

def test_invoke_finance_query(mock_orchestrator):
    """Testa uma consulta financeira, verificando se o mock é chamado corretamente."""
    # Configura o retorno do mock
    mock_response = {
        "messages": [MagicMock(content="Seu saldo é de R$ 1.000,00")]
    }
    mock_orchestrator.invoke.return_value = mock_response

    # Faz a requisição
    response = client.post("/invoke", json={"query": "qual o meu saldo?"})

    # Verifica o resultado
    assert response.status_code == 200
    assert response.json() == {"response": "Seu saldo é de R$ 1.000,00"}
    mock_orchestrator.invoke.assert_called_once()

def test_invoke_scheduling_query(mock_orchestrator):
    """Testa uma consulta de agendamento."""
    # Configura o retorno do mock
    mock_response = {
        "messages": [MagicMock(content="Compromisso agendado com sucesso!")]
    }
    mock_orchestrator.invoke.return_value = mock_response

    # Faz a requisição
    response = client.post("/invoke", json={"query": "marcar uma reunião"})

    # Verifica o resultado
    assert response.status_code == 200
    assert response.json() == {"response": "Compromisso agendado com sucesso!"}
    mock_orchestrator.invoke.assert_called_once()

def test_invoke_invalid_request():
    """Testa uma requisição com corpo inválido."""
    response = client.post("/invoke", json={"invalid_key": "some value"})
    assert response.status_code == 422  # Unprocessable Entity
