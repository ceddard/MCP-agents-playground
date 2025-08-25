from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AgentInput(BaseModel):
    session_id: Optional[str] = None
    user_intent: str = Field(..., min_length=1, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


class AgentResult(BaseModel):
    agent: str
    response: str
    payload: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    citations: Optional[List[str]] = None


class AgentError(BaseModel):
    error_code: str
    message: str
    temporary: bool = True
