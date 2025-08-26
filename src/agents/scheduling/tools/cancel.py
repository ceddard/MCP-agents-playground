from langchain.agents import Tool

def cancel_appointment(query: str) -> str:
    return "Compromisso cancelado com sucesso!"

cancel_tool = Tool(
    name="cancel_appointment",
    func=cancel_appointment,
    description="Use this tool to cancel an existing appointment.",
)
