from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from .tools import scheduling_tools


def _normalize_tool(t: Tool) -> Tool:
    safe_name = t.name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
    return Tool(name=safe_name, func=t.func, description=t.description)

normalized_scheduling_tools = [_normalize_tool(t) for t in scheduling_tools]

llm = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente de agendamento com foco em eficiência e clareza. Objetivo: ajudar a planejar, coordenar e confirmar compromissos de forma prática e sem ambiguidades.\n"
            "Instruções importantes:\n"
            "- Use ferramentas sempre que precisar consultar disponibilidade, criar eventos ou validar conflitos; depois de usar uma ferramenta, explique qual foi usada e por quê.\n"
            "- Estruture a resposta assim: 1) Resumo da ação (1 frase); 2) Detalhes do agendamento (datas, horários, participantes, fuso horário); 3) Próximos passos / confirmações necessárias; 4) Ferramentas usadas.\n"
            "- Quando houver ambiguidade sobre horários ou preferências, proponha até 3 opções claras e peça confirmação.\n"
            "- Ao mencionar horários, sempre inclua o fuso horário e qualquer conversão relevante.\n"
            "- Proteja informações sensíveis do usuário e não compartilhe dados sem permissão explícita."
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in normalized_scheduling_tools])

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)

scheduling_agent_executor = AgentExecutor(agent=agent, tools=normalized_scheduling_tools, verbose=True)
