import pytest
from dotenv import load_dotenv

# Load environment variables from .env file before importing modules that use them
load_dotenv()

from langchain_core.messages import HumanMessage
from src.graph.agent_orchestrator import agent_orchestrator
from src.schemas import OrchestratorState

def test_finance_agent_routing():
    """
    Tests if a financial query is correctly routed to the Finance agent.
    """
    # Define a financial question
    query = "Qual é o meu saldo atual?"
    initial_state: OrchestratorState = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "sender": "",
    }

    # Stream the orchestrator's execution
    events = agent_orchestrator.stream(initial_state)
    
    final_state = None
    finance_agent_called = False
    for event in events:
        if "Financeiro" in event:
            finance_agent_called = True
        if "__end__" in event:
            final_state = event["__end__"]

    # Assert that the Finance agent was called
    assert finance_agent_called, "O agente Financeiro não foi chamado para uma pergunta financeira."

    # Assert that the final response contains a plausible answer
    assert final_state is not None, "O estado final não foi alcançado."
    final_message = final_state["messages"][-1].content
    assert "saldo" in final_message.lower(), f"A resposta final não continha a palavra 'saldo'. Resposta: {final_message}"

def test_scheduling_agent_routing():
    """
    Tests if a scheduling query is correctly routed to the Scheduling agent.
    """
    # Define a scheduling question
    query = "Gostaria de marcar uma reunião para amanhã às 10h."
    initial_state: OrchestratorState = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "sender": "",
    }

    # Stream the orchestrator's execution
    events = agent_orchestrator.stream(initial_state)
    
    final_state = None
    scheduling_agent_called = False
    for event in events:
        if "Agendamento" in event:
            scheduling_agent_called = True
        if "__end__" in event:
            final_state = event["__end__"]

    # Assert that the Scheduling agent was called
    assert scheduling_agent_called, "O agente de Agendamento não foi chamado para uma pergunta de agendamento."

    # Assert that the final response contains a plausible answer
    assert final_state is not None, "O estado final não foi alcançado."
    final_message = final_state["messages"][-1].content
    assert "agendamento" in final_message.lower() or "agendado" in final_message.lower(), f"A resposta final não confirmou o agendamento. Resposta: {final_message}"

