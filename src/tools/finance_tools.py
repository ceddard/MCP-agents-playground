from langchain.agents import Tool
from src.schemas import FinanceToolMeta
import httpx
from datetime import datetime, timedelta
import re
from statistics import linear_regression

def get_balance(query: str) -> str:
    """Fake function to get balance."""
    return "Seu saldo é de R$ 1.000,00"

def make_investment(query: str) -> str:
    """Fake function to make an investment."""
    return "Investimento realizado com sucesso!"

def transfer_money(query: str) -> str:
    """Fake function to transfer money."""
    return "Transferência realizada com sucesso!"

def fetch_financial_data(query: str) -> str:
    """Fetch financial data or news from the internet."""
    try:
        if "bolsa" in query.lower():
            url = "https://www.b3.com.br/"  # Exemplo: site da bolsa brasileira
        elif "dólar" in query.lower():
            url = "https://api.exchangerate-api.com/v4/latest/USD"  # Exemplo: API de câmbio
        else:
            return "Consulta não reconhecida. Tente 'bolsa' ou 'dólar'."

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        if "bolsa" in query.lower():
            return f"Dados da bolsa: {response.text[:200]}..."  # Retorna um trecho da página
        elif "dólar" in query.lower():
            data = response.json()
            return f"Cotação atual do dólar: 1 USD = {data['rates']['BRL']} BRL"
    except Exception as e:
        return f"Erro ao buscar dados: {str(e)}"

    return "Consulta finalizada, mas sem dados específicos."

def _fetch_usd_brl_timeseries(days: int = 7) -> list[tuple[str, float]]:
    """Busca série histórica simples USD->BRL para os últimos `days` dias.

    Usa API pública exchangerate.host (sem chave). Em caso de falha retorna lista vazia.
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    url = (
        f"https://api.exchangerate.host/timeseries?start_date={start_date}&end_date={end_date}&base=USD&symbols=BRL"
    )
    try:
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        series = []
        for d, v in sorted(rates.items()):
            brl = v.get("BRL")
            if isinstance(brl, (int, float)):
                series.append((d, float(brl)))
        return series
    except Exception:
        return []


def classify_usd_brl_trend_from_series(rates: list[float]) -> str:
    """Classifica tendência a partir de uma lista de cotações ordenadas por tempo.

    Heurística:
      - Calcula regressão linear simples (x = índice, y = taxa).
      - Converte slope em variação percentual média diária: slope / média(y).
      - Thresholds: > +0.25% => 'alta provável'; < -0.25% => 'queda provável'; caso contrário 'estável/incerta'.
    """
    if len(rates) < 3:
        return "dados insuficientes"
    xs = list(range(len(rates)))
    try:
        slope, intercept = linear_regression(xs, rates)
    except Exception:
        return "erro no cálculo"
    avg = sum(rates) / len(rates)
    if avg == 0:
        return "erro no cálculo"
    daily_pct = slope / avg
    if daily_pct > 0.0015:
        return "alta provável"
    if daily_pct < -0.0015:
        return "queda provável"
    return "estável/incerta"


def predict_usd_brl_trend(query: str) -> str:
    """Prevê tendência de curto prazo do USD/BRL (heurístico, NÃO é conselho).\n\n
    Aceita no texto algo como '7d', '10 dias' para ajustar a janela (padrão 7).\n
    Passos:\n
      1. Busca série histórica recente.\n
      2. Calcula regressão linear para detectar inclinação.\n
      3. Classifica a tendência (alta provável / queda provável / estável/incerta).\n
    Limitações: Heurística simples baseada apenas em slope; ignora volatilidade intradiária, macroeconomia e eventos.\n
    """
    m = re.search(r"(\d{1,2})\s*(d|dia|dias)", query.lower())
    days = int(m.group(1)) if m else 7
    days = max(3, min(days, 30))  # limites razoáveis
    series = _fetch_usd_brl_timeseries(days)
    if not series:
        return "Não foi possível obter dados recentes para USD/BRL no momento."
    dates, values = zip(*series)
    classification = classify_usd_brl_trend_from_series(list(values))
    latest = values[-1]
    change_pct = ((values[-1] / values[0]) - 1) * 100 if values[0] else 0.0
    return (
        f"Janela: {days} dias | Última cotação: {latest:.4f} BRL | Variação acumulada: {change_pct:+.2f}% | "
        f"Tendência heurística: {classification}. (Não é recomendação de investimento.)"
    )

finance_tools = [
    Tool(
    name="get_balance",
        func=get_balance,
        description="Use this tool to get the current account balance.",
    ),
    Tool(
    name="make_investment",
        func=make_investment,
        description="Use this tool to make an investment.",
    ),
    Tool(
    name="transfer_money",
        func=transfer_money,
        description="Use this tool to transfer money to another account.",
    ),
    Tool(
        name="fetch_financial_data",
        func=fetch_financial_data,
        description="Use esta ferramenta para consultar dados da bolsa de valores ou notícias sobre o dólar."
    ),
    Tool(
        name="predict_usd_brl_trend",
        func=predict_usd_brl_trend,
        description="Prevê heurísticamente se USD/BRL tende a subir, cair ou ficar estável nos próximos dias (usa séries recentes)."
    ),
]
