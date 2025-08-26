from typing import Any, Callable, Dict, Iterable, List, Literal, Mapping, Protocol
from langchain.agents import Tool
from src.schemas import PartnerInfo


class RouterChainProtocol(Protocol):
    """Protocol for a router chain-like object used by the StateGraph router.

    It must implement an `invoke` method that accepts a mapping and returns a string
    indicating the next node key.
    """

    def invoke(self, inputs: Mapping[str, Any]) -> str:  # pragma: no cover - simple protocol
        ...


class ExecutorProtocol(Protocol):
    """Protocol for an agent executor used to handle a node's work.

    The executor must expose an `invoke` method that accepts a mapping with inputs
    and returns either a dict with 'messages' or a dict with 'output'.
    """

    def invoke(self, inputs: Mapping[str, Any]) -> Any:  # pragma: no cover - simple protocol
        ...


def normalize_tool_name(name: str) -> str:
    """Return a safe, normalized function name for OpenAI functions.

    The normalized name is lowercased, spaces and hyphens become underscores and
    any characters not in [a-zA-Z0-9_-] are removed. This ensures the name
    conforms to OpenAI's function name regex: ``^[a-zA-Z0-9_-]+$``.

    Args:
        name: Original human-friendly tool name (may contain spaces, caps).

    Returns:
        A normalized, lowercased string safe to use as an OpenAI function name.
    """
    safe_name = name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ["_", "-"])
    return safe_name.lower()


def make_normalized_tools(tools: Iterable[Tool]) -> List[Tool]:
    """Create copies of the provided Tools with names normalized for OpenAI.

    This helper keeps the original tool functions and descriptions but ensures
    the ``name`` attribute matches the OpenAI function name constraints.

    Args:
        tools: Iterable of ``langchain.agents.Tool`` instances.

    Returns:
        A list of new ``Tool`` instances with normalized names.
    """
    normalized: List[Tool] = []
    for t in tools:
        safe = normalize_tool_name(t.name)
        normalized.append(Tool(name=safe, func=t.func, description=t.description))
    return normalized


def get_system_prompt(kind: Literal["finance", "scheduling", "orchestrator"]) -> str:
    """Return a reusable system prompt for the requested component.

    The prompts are written in Portuguese and designed to be concise but explicit.

    Args:
        kind: One of ``"finance"``, ``"scheduling"`` or ``"orchestrator"``.

    Returns:
        A system prompt string appropriate for the requested component.
    """
    if kind == "finance":
        return (
            "Você é um assistente financeiro especializado em contas pessoais, investimentos e transações. "
            "Se utilizar uma das ferramentas disponíveis, invoque-a com os parâmetros apropriados e então retorne o resultado formatado para o usuário. "
            "Se for uma operação que consulta ou modifica dados (ex.: saldo, transferência, investimento), prefira usar a ferramenta. "
            "Se oferecer recomendações, seja claro sobre suposições e riscos."
        )

    if kind == "scheduling":
        return (
            "Você é um assistente de agendamento. Ajude o usuário a marcar, reagendar e cancelar compromissos. "
            "Confirme datas/horários com clareza, valide ambiguidade (pergunte se faltar informação) e, quando executar uma ação, descreva o resultado e o próximo passo."
        )

    # orchestrator
    return (
        "Você é um orquestrador de agentes cujo trabalho é decidir, com precisão, qual dos agentes especializados deve receber a pergunta do usuário. "
        "Responda estritamente com uma das duas palavras: 'Financeiro' ou 'Agendamento' — nada mais. "
        "Baseie-se somente no conteúdo da pergunta para tomar a decisão. "
        "Se a pergunta for sobre dinheiro, contas, investimentos, transações, saldos ou produtos financeiros, escolha 'Financeiro'. "
        "Se a pergunta for sobre marcar, reagendar, cancelar ou informações sobre compromissos e horários, escolha 'Agendamento'."
    )


def make_router_condition(router_chain: RouterChainProtocol) -> Callable[[Mapping[str, Any]], str]:
    """Create a router condition callable for use with StateGraph.

    The callable will receive the current state mapping (containing a `messages` list)
    and return the string key that identifies the next node in the graph.

    Args:
        router_chain: An object implementing ``invoke(inputs) -> str``.

    Returns:
        A function taking `state` and returning the routing key (string).
    """

    def router_condition(state: Mapping[str, Any]) -> str:
        return router_chain.invoke({"input": state["messages"][-1].content})

    return router_condition


def make_agent_node(executor: ExecutorProtocol) -> Callable[[Mapping[str, Any]], Dict[str, Any]]:
    """Create a StateGraph node function that delegates to an AgentExecutor.

    The node function expects the graph `state` mapping and will call
    ``executor.invoke({'input': <user message>})``. The executor's response may
    be in different shapes depending on the executor implementation; this
    factory normalizes to the graph-expected shape:

        {"messages": [BaseMessage(content=<string>, type="ai")]}

    Args:
        executor: An object exposing an ``invoke(inputs)`` method. The return
            value from ``invoke`` can be either a mapping with a 'messages'
            sequence (where the last message's .content will be used) or a
            mapping with an 'output' key.

    Returns:
        A callable which accepts `state` and returns a dict with a 'messages'
        list containing a single `BaseMessage`.
    """

    def agent_node(state: Mapping[str, Any]) -> Dict[str, Any]:
        result = executor.invoke({"input": state["messages"][-1].content})

        # Normalize the result into a message content string
        if isinstance(result, dict) and "messages" in result:
            content = result["messages"][-1].content
        else:
            content = result.get("output", "") if isinstance(result, dict) else str(result)

        from langchain_core.messages import BaseMessage

        return {"messages": [BaseMessage(content=content, type="ai")]}

    return agent_node
