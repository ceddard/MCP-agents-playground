from langchain.agents import Tool
from src.database.crud import create_finance
from src.database.models import SessionLocal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

class TransferDetails(BaseModel):
    """Informações para registrar uma transferência."""
    amount: float = Field(description="O valor da transferência")
    recipient: str = Field(description="O destinatário da transferência")

def transfer_money(query: str) -> str:
    """
    Analisa a consulta para extrair detalhes da transferência e a registra no banco de dados.
    """
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(TransferDetails)
        
        details = structured_llm.invoke(f"Extraia os detalhes da seguinte solicitação de transferência: '{query}'")

        db = SessionLocal()
        # Supondo um user_id fixo por enquanto
        create_finance(db, user_id="user1", amount=-details.amount, description=f"Transferência para {details.recipient}", date=datetime.now(), time=datetime.now().strftime('%H:%M'))
        db.close()
        
        return "Transferência registrada com sucesso!"
    except Exception as e:
        return f"Erro ao registrar transferência: {e}"

transfer_tool = Tool(
    name="transfer_money",
    func=transfer_money,
    description="Use esta ferramenta para registrar uma nova transferência de dinheiro.",
)
