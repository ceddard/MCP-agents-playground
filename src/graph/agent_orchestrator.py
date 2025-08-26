from typing import Annotated, Sequence
from typing_extensions import TypedDict
import operator
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.agents.finance.agent import finance_agent_executor
from src.agents.scheduling.agent import scheduling_agent_executor
from src.agents.agent_factory import set_current_user
from src.schemas import OrchestratorState
from functools import partial
from src.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT


# Helper function to create a router for the graph
def create_agent_router(llm, system_prompt, agents):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{messages}"),
        ]
    ).partial(agents=", ".join(agents))
    return prompt | llm | StrOutputParser()

# Function to create the agent orchestrator graph
def create_agent_orchestrator():
    # Initialize LLM
    llm = ChatOpenAI(temperature=0, model="gpt-4-turbo")

    # Define agents and their corresponding tools
    agents = {
        "Financeiro": finance_agent_executor,
        "Agendamento": scheduling_agent_executor,
    }

    # Create the router chain
    router_chain = create_agent_router(llm, ORCHESTRATOR_SYSTEM_PROMPT, agents.keys())

    # Define the nodes for the graph
    def agent_node(state: OrchestratorState, agent_name: str):
        agent_executor = agents[agent_name]
        # Definir user_id de contexto para injeção automática em ferramentas
        uid = state.get("user_id") if isinstance(state, dict) else None
        if uid:
            set_current_user(uid)
        # AgentExecutors built by `build_agent_executor` expect an 'input' key.
        last_msg = state["messages"][-1]
        # Pass the text content as the 'input' to the agent executor
        result = agent_executor.invoke({"input": last_msg.content})
        # Ensure the output is a BaseMessage
        if isinstance(result, dict) and "output" in result:
            message = HumanMessage(content=result["output"], name=agent_name)
        else:
            message = HumanMessage(content=str(result), name=agent_name)
        return {"messages": [message], "sender": agent_name}

    def router_node(state: OrchestratorState):
        # Get the last message from the state
        last_message = state["messages"][-1]
        # The router needs to decide the next agent based on the user's query
        # which is the first message in this implementation
        user_query = state["messages"][0].content
        
        # Invoke the router to decide the next agent
        next_agent = router_chain.invoke({"messages": [HumanMessage(content=user_query)]})
        
        if next_agent == "END":
            return {"next_agent": "END"}
        return {"next_agent": next_agent}

    # Build the graph
    workflow = StateGraph(OrchestratorState)

    # Add nodes for each agent
    for agent_name in agents.keys():
        workflow.add_node(
            agent_name,
            partial(agent_node, agent_name=agent_name),
        )

    # Add the router node
    workflow.add_node("router", router_node)

    # Set the entry point
    workflow.set_entry_point("router")

    # Add edges from the router to the agents
    for agent_name in agents.keys():
        workflow.add_edge(agent_name, "router")

    # Add conditional edges from the router
    workflow.add_conditional_edges(
        "router",
        lambda state: state["next_agent"],
        {
            "Financeiro": "Financeiro",
            "Agendamento": "Agendamento",
            "END": END,
        },
    )

    # Compile the graph
    return workflow.compile()

# Create the orchestrator instance
agent_orchestrator = create_agent_orchestrator()
