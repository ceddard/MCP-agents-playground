from .tools import scheduling_tools
from src.agents.agent_factory import build_agent_executor
from src.prompts.scheduling import SCHEDULING_SYSTEM_PROMPT

scheduling_agent_executor = build_agent_executor(
    system_prompt=SCHEDULING_SYSTEM_PROMPT,
    tools=scheduling_tools,
    temperature=0.0,
    verbose=True,
)
