from langchain.agents import Tool

def get_balance(query: str) -> str:
    return "Seu saldo é de R$ 1.000,00"

balance_tool = Tool(
    name="get_balance",
    func=get_balance,
    description="Use this tool to get the current account balance.",
)
