from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from src.tools.scheduling_tools import scheduling_tools
from langchain.agents import Tool

# Normalize tool names to match OpenAI functions pattern
def _normalize_tool(t: Tool) -> Tool:
    safe_name = t.name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
    return Tool(name=safe_name, func=t.func, description=t.description)

normalized_scheduling_tools = [_normalize_tool(t) for t in scheduling_tools]

llm = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Você é um assistente de agendamento."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in normalized_scheduling_tools])

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)

scheduling_agent_executor = AgentExecutor(agent=agent, tools=normalized_scheduling_tools, verbose=True)
