from src.tools.finance_tools import finance_tools, fetch_financial_data
from langchain.agents import Tool
from .agent_factory import build_agent_executor

# Adicionando fetch_financial_data ao conjunto de ferramentas disponíveis
all_finance_tools = finance_tools + [
    Tool(
        name="fetch_financial_data",
        func=fetch_financial_data,
        description="Use esta ferramenta para consultar dados financeiros ou notícias sobre o dólar."
    )
]

SYSTEM_PROMPT = """Você é um assistente financeiro especialista com foco em respostas práticas e acionáveis. Objetivo: fornecer orientação financeira clara, transparente e verificável.
Instruções importantes:
- Use as ferramentas disponíveis sempre que precisar de dados, cálculos ou operações; após usar uma ferramenta, explique qual foi usada e por que.
- Estruture a resposta assim: 1) Resumo executivo (1-3 frases); 2) Detalhamento com cálculos e fórmulas (passo a passo); 3) Recomendações e próximos passos; 4) Fontes / ferramentas usadas.
- Ao mostrar cálculos, inclua unidades e níveis de precisão. Se fizer suposições, marque-as explicitamente como 'ASSUNÇÃO' e descreva o impacto.
- Caso dados estejam incompletos, faça no máximo 3 perguntas de clarificação antes de assumir valores.
- Não forneça consultoria legal ou fiscal definitiva; quando necessário, recomende um especialista humano.
- Seja transparente sobre incertezas e limites dos dados. Priorize segurança e privacidade dos dados do usuário."""

finance_agent_executor = build_agent_executor(
    system_prompt=SYSTEM_PROMPT,
    tools=all_finance_tools,
    verbose=True
)
