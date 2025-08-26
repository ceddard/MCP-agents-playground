import pytest

# Adiciona o diretório raiz ao path para que possamos importar de `src`
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.finance.tools.balance import get_balance
from src.agents.finance.tools.investment import make_investment
from src.agents.finance.tools.transfer import transfer_money
from src.agents.finance.tools.trend import classify_usd_brl_trend_from_series
from src.agents.scheduling.tools.schedule import schedule_appointment
from src.agents.scheduling.tools.reschedule import reschedule_appointment
from src.agents.scheduling.tools.cancel import cancel_appointment

# Testes para as ferramentas financeiras
def test_get_balance():
    assert get_balance("") == "Seu saldo é de R$ 1.000,00"

def test_make_investment():
    assert make_investment("") == "Investimento realizado com sucesso!"

def test_transfer_money():
    assert transfer_money("") == "Transferência realizada com sucesso!"

# Testes para as ferramentas de agendamento
def test_schedule_appointment():
    assert schedule_appointment("") == "Compromisso agendado com sucesso!"

def test_reschedule_appointment():
    assert reschedule_appointment("") == "Compromisso reagendado com sucesso!"

def test_cancel_appointment():
    assert cancel_appointment("") == "Compromisso cancelado com sucesso!"


# --------- Testes de classificação de tendência USD/BRL (heurístico) ---------

@pytest.mark.parametrize(
    "series,expected",
    [
        ([5.00, 5.01, 5.02, 5.03, 5.05], "alta provável"),
        ([5.10, 5.08, 5.06, 5.05, 5.04], "queda provável"),
        ([5.00, 5.001, 5.0005, 5.001], "estável/incerta"),
        ([5.00, 5.10], "dados insuficientes"),
    ],
)
def test_classify_usd_brl_trend_from_series(series, expected):
    assert classify_usd_brl_trend_from_series(series) == expected
