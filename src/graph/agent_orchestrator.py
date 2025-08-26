from typing import Annotated, Sequence, Literal
from pydantic import BaseModel, Field
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from langchain_core.output_parsers import StrOutputParser
from src.agents import finance_agent_executor, scheduling_agent_executor
from src.schemas import OrchestratorConfig, AgentState  # Usar o modelo compartilhado para validação
from src.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT
from src.graph.evaluator.evaluator_node import Evaluator

# Substituir AgentState por um modelo Pydantic
# class AgentState(BaseModel):
#     messages: Sequence[BaseMessage] = Field(..., description="Sequência de mensagens trocadas pelo agente.")
#     next: Literal["Financeiro", "Agendamento"] = Field(..., description="Próximo nó a ser executado.")


def create_agent_orchestrator():
    llm = ChatOpenAI(temperature=0)

    prompt = ChatPromptTemplate.from_template(ORCHESTRATOR_SYSTEM_PROMPT + "\n\nPergunta do usuário: {input}")

    router_chain = prompt | llm | StrOutputParser()

    def router(state: AgentState):
        next_node = router_chain.invoke({"input": state.messages[-1].content})
        return {"next": next_node}

    # Função auxiliar usada apenas para a condição das arestas condicionais:
    def router_condition(state: AgentState):
        # Retorna somente a chave de roteamento (string)
        return router_chain.invoke({"input": state["messages"][-1].content})
    def finance_node(state: AgentState):
        result = finance_agent_executor.invoke({"input": state.messages[-1].content})
        return {"messages": [BaseMessage(content=result["output"], type="ai")]}

    def scheduling_node(state: AgentState):
        result = scheduling_agent_executor.invoke({"input": state["messages"][-1].content})
        return {"messages": [BaseMessage(content=result["output"], type="ai")]}

    # Atualizar a função evaluator_node para usar o Evaluator diretamente
    def evaluator_node(state: AgentState):
        evaluator = Evaluator(llm)
        return evaluator.evaluate(state)

    workflow = StateGraph(AgentState)
    workflow.add_node("Financeiro", finance_node)
    workflow.add_node("Agendamento", scheduling_node)
    workflow.add_node("Evaluator", evaluator_node)
    
    # Adiciona o nó 'router' ao grafo
    workflow.add_node("router", router)

    # O ponto de entrada agora chama a função router
    workflow.set_entry_point("Evaluator")

    # Adiciona as arestas condicionais a partir do roteador
    workflow.add_conditional_edges(
        "router",
        router_condition,
        {
            "Financeiro": "Financeiro",
            "Agendamento": "Agendamento",
        },
    )
    
    # Ajusta as arestas para garantir que o nó 'Evaluator' seja sempre o último
    workflow.add_edge("Financeiro", "Evaluator")
    workflow.add_edge("Agendamento", "Evaluator")

    # Atualiza as arestas condicionais para finalizar apenas após o 'Evaluator'
    workflow.add_conditional_edges(
        "Evaluator",
        router_condition,
        {
            "finalizar": END,
            "perguntar_usuario": "router",
            "trocar_para_financeiro": "Financeiro",
            "trocar_para_agendamento": "Agendamento",
        },
    )

    return workflow.compile()

agent_orchestrator = create_agent_orchestrator()
