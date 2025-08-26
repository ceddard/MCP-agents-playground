from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from typing import Sequence, Literal, Optional, TypedDict
from uuid import uuid4
from datetime import date
import operator
from typing_extensions import Annotated

# Modelo migrado de src/__init__.py
class AppConfig(BaseModel):
    """Aplicação: configurações mínimas compartilhadas."""
    app_name: str = "MCP-agents-playground"
    debug: bool = False
    default_locale: Optional[str] = "pt-BR"

# Modelo migrado de src/graph/agent_orchestrator.py
class OrchestratorConfig(BaseModel):
    """Configuração mínima para o orquestrador."""
    default_next: Literal["Financeiro", "Agendamento"] = "Financeiro"

# Modelo migrado de src/tools/finance_tools.py
class FinanceToolMeta(BaseModel):
    """Metadados simples para ferramentas financeiras."""
    name: str
    description: str

# Modelo migrado de src/tools/scheduling_tools.py
class SchedulingToolMeta(BaseModel):
    """Metadados simples para ferramentas de agendamento."""
    name: str
    timezone: str = "UTC"

# Modelo migrado de src/utils/design_partner.py
class PartnerInfo(BaseModel):
    """Informações mínimas sobre um parceiro de design."""
    partner_name: str
    contact_email: str | None = None

# Modelo migrado de src/agents/__init__.py
class AgentMeta(BaseModel):
    """Informações mínimas sobre um agente."""
    name: str
    version: str = "0.0.1"

class AgentState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Identificador único para cada chamada.")
    user_id: Optional[str] = Field(..., description="Identificador do usuário associado ao estado.")
    messages: Sequence[BaseMessage] = Field(..., description="Sequência de mensagens trocadas pelo agente.")
    next: Literal["Financeiro", "Agendamento"] = Field(..., description="Próximo nó a ser executado.")

class ScheduleBase(BaseModel):
    user_id: str
    date: date
    time: str
    location: str
    description: str

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int

    class Config:
        orm_mode = True

class ScheduleInput(BaseModel):
    user_id: str
    date: str
    time: str
    location: str
    description: str

class ListSchedulesInput(BaseModel):
    user_id: str

class ModifyScheduleInput(BaseModel):
    schedule_id: int
    new_date: str
    new_time: str
    new_location: str
    new_description: str

class RemoveScheduleInput(BaseModel):
    schedule_id: int

class GetBalanceInput(BaseModel):
    user_id: str

class AddTransactionInput(BaseModel):
    user_id: str
    amount: float
    description: str

# State for the Orchestrator Graph
class OrchestratorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    sender: str
    user_id: str
