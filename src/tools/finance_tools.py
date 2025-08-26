from langchain.agents import Tool
from src.database.crud import create_finance, get_finances
from src.database.session import get_db
from datetime import datetime
import json

def get_balance(user_id: str) -> str:
    """Use this tool to get the current account balance for a user."""
    db = next(get_db())
    finances = get_finances(db, user_id=user_id)
    balance = sum(f.amount for f in finances)
    return f"O saldo atual para o usuário {user_id} é de R$ {balance:.2f}"

def add_transaction(user_id: str, amount: float, description: str) -> str:
    """Use this tool to add a new financial transaction (income or expense)."""
    db = next(get_db())
    now = datetime.now()
    create_finance(db, user_id=user_id, amount=amount, description=description, date=now, time=now.strftime("%H:%M:%S"))
    return f"Transação de R$ {amount:.2f} adicionada para o usuário {user_id} com a descrição: '{description}'."

finance_tools = [
    Tool(
        name="get_balance",
        func=lambda query: get_balance(json.loads(query)["user_id"]),
        description="Use esta ferramenta para obter o saldo da conta atual de um usuário. Requer 'user_id'.",
    ),
    Tool(
        name="add_transaction",
        func=lambda query: add_transaction(**json.loads(query)),
        description="Use esta ferramenta para adicionar uma nova transação financeira. Requer 'user_id', 'amount' e 'description'.",
    ),
]
