from .tools import finance_tools
from src.agents.agent_factory import build_agent_executor
from src.prompts.finance import FINANCE_SYSTEM_PROMPT

finance_agent_executor = build_agent_executor(
    system_prompt=FINANCE_SYSTEM_PROMPT,
    tools=finance_tools,
    temperature=0.0,
    verbose=True,
)
