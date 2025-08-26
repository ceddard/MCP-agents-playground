from langchain.agents import Tool

def schedule_appointment(query: str) -> str:
    return "Compromisso agendado com sucesso!"

schedule_tool = Tool(
    name="schedule_appointment",
    func=schedule_appointment,
    description="Use this tool to schedule a new appointment.",
)
