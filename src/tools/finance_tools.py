from langchain.agents import Tool

def get_balance(query: str) -> str:
    """Fake function to get balance."""
    return "Seu saldo é de R$ 1.000,00"

def make_investment(query: str) -> str:
    """Fake function to make an investment."""
    return "Investimento realizado com sucesso!"

def transfer_money(query: str) -> str:
    """Fake function to transfer money."""
    return "Transferência realizada com sucesso!"

finance_tools = [
    Tool(
    name="get_balance",
        func=get_balance,
        description="Use this tool to get the current account balance.",
    ),
    Tool(
    name="make_investment",
        func=make_investment,
        description="Use this tool to make an investment.",
    ),
    Tool(
    name="transfer_money",
        func=transfer_money,
        description="Use this tool to transfer money to another account.",
    ),
]
