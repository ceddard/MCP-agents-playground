from langchain.agents import Tool
from src.database.crud import create_schedule
from src.database.models import SessionLocal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# Modelo Pydantic para extração de informações
class ScheduleDetails(BaseModel):
    """Informações extraídas para agendar um compromisso."""
    date: str = Field(description="A data do compromisso, formato DD/MM/YYYY")
    time: str = Field(description="A hora do compromisso, formato HH:MM")
    location: str = Field(description="O local do compromisso")
    description: str = Field(description="A descrição do compromisso")

def schedule_appointment(query: str) -> str:
    """
    Analisa a consulta usando um LLM para extrair detalhes do agendamento e o salva no banco de dados.
    """
    try:
        # Configura o LLM para extrair dados estruturados
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(ScheduleDetails)

        # Invoca o LLM para extrair os detalhes da consulta
        details = structured_llm.invoke(f"Extraia os detalhes do seguinte pedido de agendamento: '{query}'")

        date = datetime.strptime(details.date, '%d/%m/%Y')

        db = SessionLocal()
        # Supondo um user_id fixo por enquanto
        create_schedule(db, user_id="user1", date=date, time=details.time, location=details.location, description=details.description)
        db.close()
        
        return "Compromisso agendado com sucesso no banco de dados!"
    except Exception as e:
        return f"Erro ao agendar compromisso: {e}"

schedule_tool = Tool(
    name="schedule_appointment",
    func=schedule_appointment,
    description="Use esta ferramenta para agendar um novo compromisso a partir de uma consulta em linguagem natural.",
)
