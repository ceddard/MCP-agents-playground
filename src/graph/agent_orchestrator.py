from typing import TypedDict, Annotated, Sequence, Literal
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.agents import finance_agent_executor, scheduling_agent_executor

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: Literal["Financeiro", "Agendamento"]

def create_agent_orchestrator():
    llm = ChatOpenAI(temperature=0)

    prompt = ChatPromptTemplate.from_template(
        """Você é um orquestrador de agentes. Sua função é encaminhar a pergunta do usuário para o agente correto.
        Responda apenas com 'Financeiro' ou 'Agendamento'.

        Pergunta do usuário: {input}"""
    )

    router_chain = prompt | llm | StrOutputParser()

    def router(state: AgentState):
        # Usa a LLM para decidir qual o próximo nó e retorna um estado (dict)
        next_node = router_chain.invoke({"input": state["messages"][-1].content})
        return {"next": next_node}

    # Função auxiliar usada apenas para a condição das arestas condicionais:
    def router_condition(state: AgentState):
        # Retorna somente a chave de roteamento (string)
        return router_chain.invoke({"input": state["messages"][-1].content})
    def finance_node(state: AgentState):
        result = finance_agent_executor.invoke({"input": state["messages"][-1].content})
        return {"messages": [BaseMessage(content=result["output"], type="ai")]}

    def scheduling_node(state: AgentState):
        result = scheduling_agent_executor.invoke({"input": state["messages"][-1].content})
        return {"messages": [BaseMessage(content=result["output"], type="ai")]}

    workflow = StateGraph(AgentState)
    workflow.add_node("Financeiro", finance_node)
    workflow.add_node("Agendamento", scheduling_node)
    
    # Adiciona o nó 'router' ao grafo
    workflow.add_node("router", router)

    # O ponto de entrada agora chama a função router
    workflow.set_entry_point("router")

    # Adiciona as arestas condicionais a partir do roteador
    workflow.add_conditional_edges(
        "router",
        router_condition,
        {
            "Financeiro": "Financeiro",
            "Agendamento": "Agendamento",
        },
    )
    
    workflow.add_edge("Financeiro", END)
    workflow.add_edge("Agendamento", END)

    return workflow.compile()

agent_orchestrator = create_agent_orchestrator()
