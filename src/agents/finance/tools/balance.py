from langchain.agents import Tool
from src.database.crud import get_finances
from src.database.models import SessionLocal

def get_balance(query: str) -> str:
    """
    Calcula o saldo total com base nas transações financeiras do usuário.
    """
    try:
        db = SessionLocal()
        finances = get_finances(db, user_id="user1")
        db.close()

        if not finances:
            return "Nenhuma transação financeira encontrada."

        total_balance = sum(f.amount for f in finances)
        return f"Seu saldo atual é de R$ {total_balance:.2f}"
    except Exception as e:
        return f"Erro ao obter saldo: {e}"

balance_tool = Tool(
    name="get_balance",
    func=get_balance,
    description="Use esta ferramenta para obter o saldo atual da conta.",
)
