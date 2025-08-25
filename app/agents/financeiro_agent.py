"""Agente de Consulta Financeira: Especialista em dados e análises financeiras.

Melhorias: input/output schema, retries, e validação de saída.
"""
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .manager import llm
from .schemas import AgentInput, AgentResult, AgentError
from app.utils.circuit_breaker import is_open, record_failure, record_success


financeiro_prompt = ChatPromptTemplate.from_template(
    """
Você é um agente de consulta financeira. Sua função é responder a perguntas sobre
investimentos, mercados e finanças com base em seu conhecimento.
Seja direto e informativo.

Pergunta do usuário:
{payload}

Sua análise financeira:
"""
)

# Parser simples que retorna a string de resposta
financeiro_parser = StrOutputParser()

# Cadeia (chain) do agente financeiro
financeiro_agent_chain = financeiro_prompt | llm | financeiro_parser


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5),
       retry=retry_if_exception_type(Exception))
def _call_finance_chain(payload_text: str) -> str:
    return financeiro_agent_chain.invoke({"payload": payload_text})


def run_financeiro_agent(raw_payload: Dict[str, Any]) -> str:
    inp = AgentInput(**{"user_intent": raw_payload.get("message", "")})
    user_message = inp.user_intent
    agent_name = "consulta_financeira"
    if is_open(agent_name):
        raise RuntimeError("circuit_open: agent temporarily disabled due to repeated failures")

    try:
        resp_text = _call_finance_chain(user_message)
        record_success(agent_name)
    except Exception:
        record_failure(agent_name)
        raise
    try:
        result = AgentResult(agent="consulta_financeira", response=str(resp_text), payload=raw_payload)
        return result.response
    except Exception as e:
        err = AgentError(error_code="invalid_output", message=str(e))
        raise RuntimeError(err.json())
