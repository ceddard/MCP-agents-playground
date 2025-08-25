from typing import Callable, Dict
from .assessoria_agent import run_assessoria_agent
from .financeiro_agent import run_financeiro_agent

# Um registro (registry) para mapear nomes de agentes às suas funções de execução
# Isso torna o sistema extensível. Para adicionar um novo agente, basta
# criar o arquivo do agente e registrá-lo aqui.
AGENT_REGISTRY: Dict[str, Callable[[dict], str]] = {
    "assessoria": run_assessoria_agent,
    "consulta_financeira": run_financeiro_agent,
}

def get_agent_executor(agent_name: str) -> Callable[[dict], str] | None:
    """
    Retorna a função de execução para o agente especificado.
    """
    return AGENT_REGISTRY.get(agent_name)
