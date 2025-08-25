from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from dotenv import load_dotenv
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any

load_dotenv()

# LLM client (reads OPENAI_API_KEY from env)
llm = ChatOpenAI()

manager_agent_prompt_template = """
Você é um Manager Agent responsável por orquestrar chamadas a outros agentes especializados.  
Seu funcionamento será acessado via chamadas REST, onde cada requisição pode conter uma intenção do usuário.  
Seu papel não é responder diretamente às perguntas, mas identificar a intenção e redirecionar a solicitação para o agente mais adequado.

Funções principais:
1. Interpretar a requisição recebida (em JSON ou texto livre).
2. Identificar qual agente é o mais adequado:
   - "assessoria" → encaminhar para o **Agente de Assessoria**
   - "consulta_financeira" → encaminhar para o **Agente de Consulta Financeira**
   - Se não souber, retorne uma mensagem de erro estruturada: {{ "error": "Agente não encontrado para a solicitação." }}
3. Garantir que sempre retorna uma resposta padronizada em JSON:
   ```
   {{
      "agent_called": "<nome_do_agente>",
      "payload": {{ ...conteúdo a ser repassado... }}
   }}
   ```

Regras adicionais:
- Nunca invente agentes que não existem.
- Sempre mantenha consistência no formato JSON para que futuras integrações REST sejam confiáveis.
- Caso a intenção esteja ambígua, pergunte por clarificação em vez de escolher arbitrariamente.

Você deve atuar como um **roteador inteligente de intents** para os outros agentes.

A intenção do usuário é: {user_intent}
"""


class AgentOutputParser(BaseOutputParser):
   def parse(self, text: str):
      """Try to parse the LLM output as JSON. If it contains a mapping with
      `agent_called` and optionally `payload`, return that dict. Otherwise
      return a dict with `agent_called` set to the raw text.
      """
      raw = text.strip()
      # Attempt JSON parse
      try:
         parsed = json.loads(raw)
         if isinstance(parsed, dict) and "agent_called" in parsed:
            return parsed
      except Exception:
         parsed = None

      # Some LLMs return a JSON string inside text; try to extract JSON block
      if parsed is None:
         try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
               maybe = raw[start:end+1]
               parsed2 = json.loads(maybe)
               if isinstance(parsed2, dict) and "agent_called" in parsed2:
                  return parsed2
         except Exception:
            pass

      # fallback: return raw text as agent_called
      return {"agent_called": raw}


_manager_runnable = None


def _build_manager_runnable():
   """Build and return the LangChain runnable pipeline. This is done lazily
   so module import doesn't trigger network calls or validations that can
   raise and crash the app during import.
   """
   global _manager_runnable
   if _manager_runnable is not None:
      return _manager_runnable

   prompt = ChatPromptTemplate.from_template(manager_agent_prompt_template)
   # create the runnable pipeline (this should not call the network yet)
   _manager_runnable = prompt | llm | AgentOutputParser()
   return _manager_runnable


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.3, max=2),
       retry=retry_if_exception_type(Exception))
def _invoke_manager(user_intent: str) -> Dict[str, Any]:
   runnable = _build_manager_runnable()
   result = runnable.invoke({"user_intent": user_intent})
   return result


def decide_agent(user_intent: str) -> dict:
   """Use the LLM pipeline if available; on any error, fall back to a
   deterministic rule-based router. Always returns a JSON-serializable dict
   with keys `agent_called` and `payload`.
   """
   def _normalize_agent_name(raw: str) -> str:
      if not raw:
         return "unknown"
      s = raw.lower()
      # direct canonical
      if s in ("assessoria", "consulta_financeira", "consulta-financeira", "financeiro"):
         return s if s != "financeiro" else "consulta_financeira"
      # heuristics / synonyms
      if "assess" in s or "assessor" in s or "assessoria" in s:
         return "assessoria"
      if "finance" in s or "financ" in s or "invest" in s or "consulta" in s:
         return "consulta_financeira"
      return "unknown"

   try:
      result = _invoke_manager(user_intent)
      raw_agent = result.get("agent_called", "")
      agent_canonical = _normalize_agent_name(raw_agent)
      return {"agent_called": agent_canonical, "payload": {"message": user_intent}}
   except Exception as e:
      # Log minimal info to payload and return deterministic fallback
      intent_lower = (user_intent or "").lower()
      if "invest" in intent_lower or "investimentos" in intent_lower:
         agent = "consulta_financeira"
      elif "assessoria" in intent_lower or "assessor" in intent_lower:
         agent = "assessoria"
      else:
         agent = "unknown"
      return {"agent_called": agent, "payload": {"message": user_intent, "note": "fallback due to LLM error", "error": str(e)}}
