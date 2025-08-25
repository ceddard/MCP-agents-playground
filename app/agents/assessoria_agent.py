"""Agente de Assessoria: Especialista em fornecer conselhos gerais e direcionamento.

Melhorias:
- Validação de entrada via Pydantic
- Envoltório de timeout + retry para chamadas ao LLM
- Validação do formato de saída
"""
from typing import Dict, Any
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .manager import llm
from .schemas import AgentInput, AgentResult, AgentError
from app.utils.circuit_breaker import is_open, record_failure, record_success


assessoria_prompt = ChatPromptTemplate.from_template(
    """
Você é um agente de assessoria. Sua função é fornecer uma orientação geral e amigável
com base na solicitação do usuário. Não forneça conselhos financeiros específicos.

Solicitação do usuário:
{payload}

Sua resposta de assessoria:
"""
)

# Parser simples que retorna a string de resposta
assessoria_parser = StrOutputParser()

# Cadeia (chain) do agente de assessoria
assessoria_agent_chain = assessoria_prompt | llm | assessoria_parser


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5),
       retry=retry_if_exception_type(Exception))
def _call_llm_chain(payload_text: str) -> str:
    # simple sync wrapper; tenacity will retry on exceptions
    return assessoria_agent_chain.invoke({"payload": payload_text})


def run_assessoria_agent(raw_payload: Dict[str, Any]) -> str:
    """Execute o agente com validação e resiliencia.

    Retorna a resposta textual do agente; em caso de erro, levanta Exception
    para o chamador lidar (HTTP 500 ou fallback).
    """
    # validate input
    inp = AgentInput(**{"user_intent": raw_payload.get("message", "")})
    user_message = inp.user_intent

    agent_name = "assessoria"
    if is_open(agent_name):
        raise RuntimeError("circuit_open: agent temporarily disabled due to repeated failures")

    # call LLM with retries
    try:
        resp_text = _call_llm_chain(user_message)
        record_success(agent_name)
    except Exception as e:
        record_failure(agent_name)
        raise

    # validate/shape output
    try:
        result = AgentResult(agent="assessoria", response=str(resp_text), payload=raw_payload)
        return result.response
    except Exception as e:
        err = AgentError(error_code="invalid_output", message=str(e))
        raise RuntimeError(err.json())
