import pytest
from src.tools.scheduling_tools import (
    schedule_meeting,
    reschedule_meeting,
    cancel_meeting,
)

def test_schedule_meeting():
    assert schedule_meeting("Reunião de equipe amanhã às 10h") == "Reunião agendada com sucesso para: Reunião de equipe amanhã às 10h"

def test_reschedule_meeting():
    assert reschedule_meeting("Reunião de equipe para sexta-feira às 14h") == "Reunião reagendada com sucesso para: Reunião de equipe para sexta-feira às 14h"

def test_cancel_meeting():
    assert cancel_meeting("Reunião de equipe") == "Reunião sobre 'Reunião de equipe' cancelada com sucesso!"
