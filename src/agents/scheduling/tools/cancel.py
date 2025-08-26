from langchain.agents import Tool
from src.database.crud import delete_schedule, get_schedules
from src.database.models import SessionLocal
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

class CancelDetails(BaseModel):
    """Informações para cancelar um compromisso."""
    schedule_id: int = Field(description="O ID do compromisso a ser cancelado")

def cancel_appointment(query: str) -> str:
    """
    Analisa a consulta para extrair o ID do compromisso e o cancela no banco de dados.
    """
    db = SessionLocal()
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(CancelDetails)
        
        # Supondo um user_id fixo por enquanto
        schedules = get_schedules(db, user_id="user1")

        if not schedules:
            return "Nenhum compromisso encontrado para cancelar."

        schedules_info = "\n".join([f"ID: {s.id}, Data: {s.date.strftime('%d/%m/%Y')}, Hora: {s.time}, Local: {s.location}, Descrição: {s.description}" for s in schedules])
        
        prompt = f"Aqui estão os compromissos existentes:\n{schedules_info}\n\nCom base na consulta a seguir, extraia o ID do compromisso para cancelamento: '{query}'"
        
        details: CancelDetails = structured_llm.invoke(prompt)

        delete_schedule(db, schedule_id=details.schedule_id)
        
        return "Compromisso cancelado com sucesso!"
    except Exception as e:
        return f"Erro ao cancelar compromisso: {e}"
    finally:
        db.close()

cancel_tool = Tool(
    name="cancel_appointment",
    func=cancel_appointment,
    description="Use esta ferramenta para cancelar um compromisso existente.",
)
