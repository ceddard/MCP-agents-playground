from langchain.tools import tool
from src.database.crud import create_finance, get_finances
from src.database.session import get_db
from src.schemas import GetBalanceInput, AddTransactionInput
from datetime import datetime

@tool(args_schema=GetBalanceInput)
def get_balance(user_id: str) -> str:
    """Use this tool to get the current account balance for a user."""
    db = next(get_db())
    finances = get_finances(db, user_id=user_id)
    if not finances:
        return f"Nenhuma transação encontrada para o usuário {user_id}. Saldo é R$ 0.00"
    balance = sum(f.amount for f in finances)
    return f"O saldo atual para o usuário {user_id} é de R$ {balance:.2f}"

@tool(args_schema=AddTransactionInput)
def add_transaction(user_id: str, amount: float, description: str) -> str:
    """Use this tool to add a new financial transaction (income or expense)."""
    db = next(get_db())
    now = datetime.now()
    create_finance(db, user_id=user_id, amount=amount, description=description, date=now, time=now.strftime("%H:%M:%S"))
    return f"Transação de R$ {amount:.2f} adicionada para o usuário {user_id} com a descrição: '{description}'."

finance_tools = [
    get_balance,
    add_transaction,
]
