from langchain.agents import Tool

def make_investment(query: str) -> str:
    return "Investimento realizado com sucesso!"

investment_tool = Tool(
    name="make_investment",
    func=make_investment,
    description="Use this tool to make an investment.",
)
