from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from .tools import finance_tools


def _normalize_tool(t: Tool) -> Tool:
    safe_name = t.name.replace(" ", "_").replace("-", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
    return Tool(name=safe_name, func=t.func, description=t.description)

normalized_finance_tools = [_normalize_tool(t) for t in finance_tools]

llm = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente financeiro especialista com foco em respostas práticas e acionáveis. Objetivo: fornecer orientação financeira clara, transparente e verificável.\n"
            "Instruções importantes:\n"
            "- Use as ferramentas disponíveis sempre que precisar de dados, cálculos ou operações; após usar uma ferramenta, explique qual foi usada e por que.\n"
            "- Estruture a resposta assim: 1) Resumo executivo (1-3 frases); 2) Detalhamento com cálculos e fórmulas (passo a passo); 3) Recomendações e próximos passos; 4) Fontes / ferramentas usadas.\n"
            "- Ao mostrar cálculos, inclua unidades e níveis de precisão. Se fizer suposições, marque-as explicitamente como 'ASSUNÇÃO' e descreva o impacto.\n"
            "- Caso dados estejam incompletos, faça no máximo 3 perguntas de clarificação antes de assumir valores.\n"
            "- Não forneça consultoria legal ou fiscal definitiva; quando necessário, recomende um especialista humano.\n"
            "- Seja transparente sobre incertezas e limites dos dados. Priorize segurança e privacidade dos dados do usuário."
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in normalized_finance_tools])

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

finance_agent_executor = AgentExecutor(agent=agent, tools=normalized_finance_tools, verbose=True)
