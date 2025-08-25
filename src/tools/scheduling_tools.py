from langchain.agents import Tool

def schedule_appointment(query: str) -> str:
    """Fake function to schedule an appointment."""
    return "Compromisso agendado com sucesso!"

def reschedule_appointment(query: str) -> str:
    """Fake function to reschedule an appointment."""
    return "Compromisso reagendado com sucesso!"

def cancel_appointment(query: str) -> str:
    """Fake function to cancel an appointment."""
    return "Compromisso cancelado com sucesso!"

scheduling_tools = [
    Tool(
    name="schedule_appointment",
        func=schedule_appointment,
        description="Use this tool to schedule a new appointment.",
    ),
    Tool(
    name="reschedule_appointment",
        func=reschedule_appointment,
        description="Use this tool to reschedule an existing appointment.",
    ),
    Tool(
    name="cancel_appointment",
        func=cancel_appointment,
        description="Use this tool to cancel an existing appointment.",
    ),
]
