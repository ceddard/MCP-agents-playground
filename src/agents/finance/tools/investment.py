from langchain.agents import Tool
from src.database.crud import create_finance
from src.database.models import SessionLocal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

class InvestmentDetails(BaseModel):
    """Informações para registrar um investimento."""
    amount: float = Field(description="O valor do investimento")
    description: str = Field(description="A descrição do investimento (ex: 'compra de ações da AAPL')")

def make_investment(query: str) -> str:
    """
    Analisa a consulta para extrair detalhes do investimento e o registra no banco de dados.
    """
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(InvestmentDetails)
        
        details = structured_llm.invoke(f"Extraia os detalhes do seguinte pedido de investimento: '{query}'")

        db = SessionLocal()
        # Supondo um user_id fixo por enquanto
        create_finance(db, user_id="user1", amount=-details.amount, description=details.description, date=datetime.now(), time=datetime.now().strftime('%H:%M'))
        db.close()
        
        return "Investimento registrado com sucesso!"
    except Exception as e:
        return f"Erro ao registrar investimento: {e}"

investment_tool = Tool(
    name="make_investment",
    func=make_investment,
    description="Use esta ferramenta para registrar um novo investimento.",
)
