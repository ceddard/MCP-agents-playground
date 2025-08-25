import os
import logging
import uuid
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.agents.manager import decide_agent
from app.agents.registry import get_agent_executor
from app.orchestration.graph import run_orchestration, graph_mermaid
from app.storage.redis_storage import clear_history, _client as _redis_client

# basic structured-ish logging
logger = logging.getLogger("mcp_orchestrator")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple API key check for protected endpoints.

    Set `API_KEY` in the environment in production and clients must send
    header `X-API-Key: <value>`. If `API_KEY` is not set, the check is skipped
    (convenience for local development).
    """
    expected = os.getenv("API_KEY")
    if not expected:
        return None
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

app = FastAPI(
    title="Orquestrador de Agentes",
    description="Uma API para rotear intenções de usuários para agentes especializados.",
    version="1.0.0",
)

class UserIntent(BaseModel):
    user_intent: str

class AgentResponse(BaseModel):
    agent_called: str
    response: str
    payload_received: dict

class GraphIntent(BaseModel):
    user_intent: str
    session_id: str | None = None

class GraphExecutionResult(BaseModel):
    mode: str
    user_intent: str | None = None
    agent_called: str | None = None
    payload: dict | None = None
    agent_response: str | None = None
    error: str | None = None
    history: list[dict] | None = None
    session_id: str | None = None


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    # call next and attach header to response
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

@app.post("/execute", response_model=AgentResponse)
async def execute_agent_flow(intent: UserIntent, _=Depends(require_api_key)):
    """
    Recebe a intenção do usuário, usa o Manager Agent para decidir qual
    agente especializado chamar e, em seguida, executa esse agente.
    """
    # 1. Roteamento: O Manager Agent decide qual agente chamar
    routing_decision = decide_agent(intent.user_intent)
    agent_name = routing_decision.get("agent_called") or None
    payload = routing_decision.get("payload", {})

    # 2. Execução: Encontra e executa o agente escolhido
    if agent_name is None:
        raise HTTPException(status_code=400, detail="Manager não retornou 'agent_called'.")

    agent_executor = get_agent_executor(agent_name)
    if agent_executor is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agente '{agent_name}' não encontrado ou não especificado.",
        )

    # Executa o agente e obtém a resposta
    try:
        agent_response_content = agent_executor(payload)
        return AgentResponse(
            agent_called=agent_name,
            response=agent_response_content,
            payload_received=payload,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar o agente '{agent_name}': {e}",
        )

# O endpoint /route continua existindo para depuração, se necessário
@app.post("/route")
async def route_intent(intent: UserIntent):
    """Apenas para depuração: retorna a decisão do Manager Agent sem executar."""
    return decide_agent(intent.user_intent)


@app.post("/graph/execute", response_model=GraphExecutionResult)
async def graph_execute(intent: GraphIntent, _=Depends(require_api_key)):
    """Executa a orquestração via LangGraph (ou fallback) e retorna o estado final.

    Aceita session_id opcional para manter histórico entre chamadas.
    """
    result = run_orchestration(intent.user_intent, session_id=intent.session_id)
    return GraphExecutionResult(**result)


@app.get("/graph/mermaid")
async def graph_diagram():
    """Retorna diagrama Mermaid estático do fluxo atual."""
    return {"mermaid": graph_mermaid()}


@app.get("/health")
async def health():
    """Liveness probe - app process running."""
    return JSONResponse({"status": "ok"})


@app.get("/ready")
async def ready():
    """Readiness probe - checks Redis connectivity and basic env readiness."""
    checks = {"redis": False, "openai_key_present": False}
    # Redis ping
    try:
        checks["redis"] = bool(_redis_client.ping())
    except Exception as e:
        logger.warning("Redis readiness check failed: %s", e)
        checks["redis"] = False
    # OpenAI key presence (not validating correctness)
    checks["openai_key_present"] = bool(os.getenv("OPENAI_API_KEY"))
    ready_state = all(checks.values())
    return JSONResponse({"ready": ready_state, "checks": checks})


class ClearSessionRequest(BaseModel):
    session_id: str


@app.post("/admin/clear_session")
async def admin_clear_session(req: ClearSessionRequest, _=Depends(require_api_key)):
    """Admin endpoint to clear session history from Redis."""
    clear_history(req.session_id)
    return {"ok": True, "session_id": req.session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
