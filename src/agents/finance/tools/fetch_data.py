from langchain.agents import Tool
import httpx

def fetch_financial_data(query: str) -> str:
    try:
        if "bolsa" in query.lower():
            url = "https://www.b3.com.br/"
        elif "dólar" in query.lower():
            url = "https://api.exchangerate-api.com/v4/latest/USD"
        else:
            return "Consulta não reconhecida. Tente 'bolsa' ou 'dólar'."
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        if "bolsa" in query.lower():
            return f"Dados da bolsa: {response.text[:200]}..."
        elif "dólar" in query.lower():
            data = response.json()
            return f"Cotação atual do dólar: 1 USD = {data['rates']['BRL']} BRL"
    except Exception as e:
        return f"Erro ao buscar dados: {str(e)}"
    return "Consulta finalizada, mas sem dados específicos."

fetch_data_tool = Tool(
    name="fetch_financial_data",
    func=fetch_financial_data,
    description="Use esta ferramenta para consultar dados da bolsa de valores ou notícias sobre o dólar."
)
