from langchain.agents import Tool
from src.database.crud import update_schedule, get_schedules
from src.database.models import SessionLocal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

class RescheduleDetails(BaseModel):
    """Informações para reagendar um compromisso."""
    schedule_id: int = Field(description="O ID do compromisso a ser reagendado")
    new_date: str = Field(description="A nova data do compromisso, formato DD/MM/YYYY")
    new_time: str = Field(description="A nova hora do compromisso, formato HH:MM")
    new_location: str = Field(description="O novo local do compromisso")
    new_description: str = Field(description="A nova descrição do compromisso")

def reschedule_appointment(query: str) -> str:
    """
    Analisa a consulta para extrair detalhes do reagendamento e o atualiza no banco de dados.
    """
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(RescheduleDetails)
        
        db = SessionLocal()
        schedules = get_schedules(db, user_id="user1")
        db.close()

        if not schedules:
            return "Nenhum compromisso encontrado para reagendar."

        schedules_info = "\n".join([f"ID: {s.id}, Data: {s.date.strftime('%d/%m/%Y')}, Hora: {s.time}, Local: {s.location}, Descrição: {s.description}" for s in schedules])
        
        prompt = f"Aqui estão os compromissos existentes:\n{schedules_info}\n\nCom base na consulta a seguir, extraia os detalhes para reagendamento: '{query}'"
        
        details = structured_llm.invoke(prompt)

        new_date = datetime.strptime(details.new_date, '%d/%m/%Y')

        db = SessionLocal()
        update_schedule(db, schedule_id=details.schedule_id, new_date=new_date, new_time=details.new_time, new_location=details.new_location, new_description=details.new_description)
        db.close()
        
        return "Compromisso reagendado com sucesso!"
    except Exception as e:
        return f"Erro ao reagendar compromisso: {e}"

reschedule_tool = Tool(
    name="reschedule_appointment",
    func=reschedule_appointment,
    description="Use esta ferramenta para reagendar um compromisso existente.",
)
