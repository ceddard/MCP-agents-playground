from langchain.agents import Tool

def reschedule_appointment(query: str) -> str:
    return "Compromisso reagendado com sucesso!"

reschedule_tool = Tool(
    name="reschedule_appointment",
    func=reschedule_appointment,
    description="Use this tool to reschedule an existing appointment.",
)
