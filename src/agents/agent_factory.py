from __future__ import annotations
from typing import Sequence, Callable, Any
import contextvars
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor
_current_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_user_id", default=None)

def set_current_user(user_id: str | None):
    """Define o user_id corrente no contexto (thread-safe) para injeção automática em ferramentas."""
    _current_user_id.set(user_id)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser


def _normalize_tool(t: Tool) -> Tool:
    safe_name = t.name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
    # Wrap original func to enforce returning string and keep description intact
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

    # Wrap tools to auto-inject user_id if missing
    wrapped_tools: list[Tool] = []
    for t in normalized:
        orig_func = t.func if t.func is not None else (lambda *a, **k: "Função da ferramenta não definida")

        def make_wrapper(f: Callable[..., Any]):
            def _wrapper(*args, **kwargs):
                if "user_id" not in kwargs or kwargs.get("user_id") in (None, ""):
                    ctx_uid = _current_user_id.get()
                    if ctx_uid:
                        kwargs["user_id"] = ctx_uid
                return f(*args, **kwargs)
            return _wrapper

        wrapped = Tool(name=t.name, func=make_wrapper(orig_func), description=t.description)
        wrapped_tools.append(wrapped)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in wrapped_tools])

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

    return AgentExecutor(agent=agent, tools=wrapped_tools, verbose=verbose)


__all__ = ["build_agent_executor", "set_current_user"]
