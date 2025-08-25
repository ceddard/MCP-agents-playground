"""Orquestração de agentes usando LangGraph com memória de conversa.

Fluxo:
    start -> manager_decide -> (assessoria | consulta_financeira | unknown) -> END

Memória:
    Mantemos um histórico de turnos (lista de dicts) por `session_id` em memória
    (apenas para desenvolvimento; para produção substituir por Redis / banco).
    Cada turno adiciona:
        - {"role": "user", "content": <user_intent>}
        - {"role": "agent", "agent": <agent_called>, "content": <agent_response|erro>} (após execução)

State contract (GraphState):
    user_intent: str                      # intenção atual
    agent_called: str | None              # agente decidido
    payload: dict                         # payload repassado ao agente
    agent_response: str | None            # resposta do agente executado
    error: str | None                     # mensagem de erro se houver
    history: list[dict]                   # histórico acumulado de turnos
    session_id: str | None                # id da sessão (para armazenar em cache global)
"""
from __future__ import annotations

from typing import TypedDict, Optional, Dict, Any, List, cast

try:
    from langgraph.graph import StateGraph, END
except ImportError:  # fallback se langgraph não estiver instalado
    StateGraph = None  # type: ignore
    END = "END"  # type: ignore

from app.agents.manager import decide_agent
from app.agents.registry import get_agent_executor
from app.orchestration.router import resolve_agent_name


class GraphState(TypedDict, total=False):
    user_intent: str
    agent_called: Optional[str]
    payload: Dict[str, Any]
    agent_response: Optional[str]
    error: Optional[str]
    history: List[Dict[str, Any]]
    session_id: Optional[str]


def _node_manager(state: GraphState) -> GraphState:
    ui = state.get("user_intent", "")
    # (Futuro) poderíamos enriquecer o prompt do manager com o histórico.
    decision = decide_agent(ui)
    new_state = {
        **state,
        "agent_called": decision.get("agent_called"),
        "payload": decision.get("payload", {}),
    }
    return cast(GraphState, new_state)


def _node_assessoria(state: GraphState) -> GraphState:
    exec_fn = get_agent_executor("assessoria")
    try:
        resp = exec_fn(state.get("payload", {})) if exec_fn else None
        return _append_history({**state, "agent_response": resp}, success=True)
    except Exception as e:  # pragma: no cover
        return _append_history({**state, "error": f"assessoria_failed: {e}"}, success=False)


def _node_financeiro(state: GraphState) -> GraphState:
    exec_fn = get_agent_executor("consulta_financeira")
    try:
        resp = exec_fn(state.get("payload", {})) if exec_fn else None
        return _append_history({**state, "agent_response": resp}, success=True)
    except Exception as e:  # pragma: no cover
        return _append_history({**state, "error": f"financeiro_failed: {e}"}, success=False)


def _node_unknown(state: GraphState) -> GraphState:
    return _append_history({**state, "error": state.get("error") or "Agente desconhecido"}, success=False)


def _route_after_manager(state: GraphState) -> str:
    raw = state.get("agent_called") or ""
    return resolve_agent_name(raw)


_cached_graph = None
from app.storage.redis_storage import append_turn, get_history


def _append_history(state: GraphState, success: bool) -> GraphState:
    """Atualiza histórico em memória local e no estado."""
    history = list(state.get("history", []))
    # Apenas adiciona a parte do agente; a parte do usuário foi adicionada antes de iniciar o grafo
    entry = {
        "role": "agent",
        "agent": state.get("agent_called"),
        "success": success,
        "content": state.get("agent_response") if success else state.get("error"),
    }
    history.append(entry)
    session_id = state.get("session_id")
    if session_id:
        append_turn(session_id, entry)
    state["history"] = history  # mutate accepted for graph state
    return state


def build_graph():
    global _cached_graph
    if _cached_graph is not None:
        return _cached_graph
    if StateGraph is None:
        raise RuntimeError("LangGraph não instalado. Instale 'langgraph' para usar a orquestração.")
    graph = StateGraph(GraphState)
    graph.add_node("manager", _node_manager)
    graph.add_node("assessoria", _node_assessoria)
    graph.add_node("consulta_financeira", _node_financeiro)
    graph.add_node("unknown", _node_unknown)
    graph.set_entry_point("manager")
    graph.add_conditional_edges("manager", _route_after_manager, {
        "assessoria": "assessoria",
        "consulta_financeira": "consulta_financeira",
        "unknown": "unknown",
    })
    graph.add_edge("assessoria", END)
    graph.add_edge("consulta_financeira", END)
    graph.add_edge("unknown", END)
    _cached_graph = graph.compile()
    return _cached_graph


def run_orchestration(user_intent: str, session_id: str | None = None) -> Dict[str, Any]:
    """Executa o grafo e retorna um dicionário normalizado incluindo histórico.

    Se `session_id` for fornecido, o histórico acumulado dessa sessão é carregado
    e atualizado. Para produção, substituir armazenamento em memória por backend
    persistente.
    """
    try:
        compiled = build_graph()
    except Exception as e:
        # fallback: usa apenas o decide_agent direto
        decision = decide_agent(user_intent)
        history = []
        if session_id:
            history = list(get_history(session_id))
        history.append({"role": "user", "content": user_intent})
        return {
            "mode": "fallback-no-graph",
            "agent_called": decision.get("agent_called"),
            "payload": decision.get("payload"),
            "agent_response": None,
            "error": str(e),
            "history": history,
            "session_id": session_id,
        }

    # Prepara histórico inicial
    prior_history: List[Dict[str, Any]] = []
    if session_id:
        prior_history = list(get_history(session_id))
    # adiciona turno do usuário
    prior_history.append({"role": "user", "content": user_intent})
    if session_id:
        append_turn(session_id, {"role": "user", "content": user_intent})

    state: GraphState = {"user_intent": user_intent, "history": prior_history, "session_id": session_id}
    final_state = compiled.invoke(state)  # nodes append agent response to history
    return {
        "mode": "graph",
        "user_intent": final_state.get("user_intent"),
        "agent_called": final_state.get("agent_called"),
        "payload": final_state.get("payload"),
        "agent_response": final_state.get("agent_response"),
        "error": final_state.get("error"),
        "history": final_state.get("history"),
        "session_id": session_id,
    }


def graph_mermaid() -> str:
    """Retorna um diagrama Mermaid estático representando o fluxo."""
    return (
        "flowchart TD\n"
        "  A[manager_decide] -->|assessoria| B[assessoria]\n"
        "  A -->|consulta_financeira| C[financeiro]\n"
        "  A -->|unknown| D[unknown]\n"
    )
