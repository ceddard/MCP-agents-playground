from __future__ import annotations
from typing import Sequence
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser


def _normalize_tool(t: Tool) -> Tool:
    safe_name = t.name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
    return Tool(name=safe_name, func=t.func, description=t.description)


def build_agent_executor(
    system_prompt: str,
    tools: Sequence[Tool],
    temperature: float = 0.0,
    verbose: bool = True,
) -> AgentExecutor:
    """Cria um AgentExecutor padronizado com suporte a OpenAI function calling.

    Args:
        system_prompt: Mensagem de sistema detalhando o papel e instruções.
        tools: Sequência de ferramentas (langchain.agents.Tool).
        temperature: Temperatura do modelo.
        verbose: Flag de verbosidade.
    """
    llm = ChatOpenAI(temperature=temperature)
    normalized = [_normalize_tool(t) for t in tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in normalized])

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

    return AgentExecutor(agent=agent, tools=normalized, verbose=verbose)


__all__ = ["build_agent_executor"]
