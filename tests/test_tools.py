import pytest

# Adiciona o diretório raiz ao path para que possamos importar de `src`
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.finance_tools import get_balance, make_investment, transfer_money
from src.tools.scheduling_tools import schedule_appointment, reschedule_appointment, cancel_appointment

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
