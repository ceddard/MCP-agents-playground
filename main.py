from fastapi import FastAPI
from pydantic import BaseModel
from src.graph import agent_orchestrator
from typing import cast
from src.schemas import OrchestratorState
from langchain_core.messages import HumanMessage
from src.agents import finance_agent_executor, scheduling_agent_executor
from dotenv import load_dotenv
import os
import uvicorn

# Carrega as variáveis de ambiente do arquivo .env no início do script
load_dotenv()

# Verifica se a chave da API da OpenAI está configurada
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "A variável de ambiente OPENAI_API_KEY não foi definida. "
        "Por favor, crie um arquivo .env e adicione a linha: OPENAI_API_KEY='sua-chave-aqui'"
    )

app = FastAPI(
    title="Agent Orchestrator API",
    description="API para interagir com um sistema de agentes orquestrados.",
    version="1.0.0",
)

class QueryRequest(BaseModel):
    query: str
    user_id: str

class QueryResponse(BaseModel):
    response: str

@app.post("/invoke", response_model=QueryResponse)
def invoke_agent(request: QueryRequest):
    """Endpoint principal que envia a consulta para o orquestrador de agentes."""
    initial_state = {
        "messages": [HumanMessage(content=request.query)],
        "next_agent": "",
        "sender": "usuario",
        "user_id": request.user_id,
    }

    try:
        result = agent_orchestrator.invoke(cast(OrchestratorState, initial_state))
        response_content = result["messages"][-1].content
    except Exception:
        # Fallback simples baseado em palavra-chave
        q = request.query.lower()
        if any(k in q for k in ("invest", "saldo", "conta", "finan")):
            result = finance_agent_executor.invoke({"input": request.query})
        else:
            result = scheduling_agent_executor.invoke({"input": request.query})
        response_content = (
            result["messages"][-1].content if "messages" in result else result.get("output", "")
        )

    return QueryResponse(response=response_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
