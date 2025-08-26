from langchain.agents import Tool

def transfer_money(query: str) -> str:
    return "Transferência realizada com sucesso!"

transfer_tool = Tool(
    name="transfer_money",
    func=transfer_money,
    description="Use this tool to transfer money to another account.",
)
