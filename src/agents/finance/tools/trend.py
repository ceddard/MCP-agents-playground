from langchain.agents import Tool
from datetime import datetime, timedelta
import httpx
import re
from statistics import linear_regression


def _fetch_usd_brl_timeseries(days: int = 7) -> list[tuple[str, float]]:
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
    m = re.search(r"(\d{1,2})\s*(d|dia|dias)", query.lower())
    days = int(m.group(1)) if m else 7
    days = max(3, min(days, 30))
    series = _fetch_usd_brl_timeseries(days)
    if not series:
        return "Não foi possível obter dados recentes para USD/BRL no momento."
    _, values = zip(*series)
    classification = classify_usd_brl_trend_from_series(list(values))
    latest = values[-1]
    change_pct = ((values[-1] / values[0]) - 1) * 100 if values[0] else 0.0
    return (
        f"Janela: {days} dias | Última cotação: {latest:.4f} BRL | Variação acumulada: {change_pct:+.2f}% | "
        f"Tendência heurística: {classification}. (Não é recomendação de investimento.)"
    )

trend_tool = Tool(
    name="predict_usd_brl_trend",
    func=predict_usd_brl_trend,
    description="Prevê heurísticamente se USD/BRL tende a subir, cair ou ficar estável nos próximos dias (usa séries recentes)."
)
