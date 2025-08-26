import pytest
from unittest.mock import patch, MagicMock
from src.tools.finance_tools import (
    get_balance,
    make_investment,
    transfer_money,
    fetch_financial_data,
    predict_usd_brl_trend,
    _fetch_usd_brl_timeseries,
    classify_usd_brl_trend_from_series,
)

def test_get_balance():
    assert get_balance("") == "Seu saldo é de R$ 1.000,00"

def test_make_investment():
    assert make_investment("") == "Investimento realizado com sucesso!"

def test_transfer_money():
    assert transfer_money("") == "Transferência realizada com sucesso!"

@patch('httpx.get')
def test_fetch_financial_data_bolsa_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Notícias da bolsa..."
    mock_get.return_value = mock_response
    assert "Dados da bolsa: Notícias da bolsa..." in fetch_financial_data("notícias da bolsa")

@patch('httpx.get')
def test_fetch_financial_data_dolar_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"BRL": 5.25}}
    mock_get.return_value = mock_response
    assert "Cotação atual do dólar: 1 USD = 5.25 BRL" in fetch_financial_data("cotação do dólar")

@patch('httpx.get')
def test_fetch_financial_data_failure(mock_get):
    mock_get.side_effect = Exception("Test error")
    assert "Erro ao buscar dados: Test error" in fetch_financial_data("dólar")

def test_classify_usd_brl_trend_from_series():
    assert classify_usd_brl_trend_from_series([1, 2, 3]) == "alta provável"
    assert classify_usd_brl_trend_from_series([3, 2, 1]) == "queda provável"
    assert classify_usd_brl_trend_from_series([1, 1.001, 1.002]) == "estável/incerta"
    assert classify_usd_brl_trend_from_series([1, 2]) == "dados insuficientes"

@patch('src.tools.finance_tools._fetch_usd_brl_timeseries')
def test_predict_usd_brl_trend(mock_fetch):
    mock_fetch.return_value = [("2025-08-25", 5.20), ("2025-08-26", 5.25)]
    result = predict_usd_brl_trend("previsão do dólar para 2 dias")
    assert "Tendência heurística:" in result
    assert "5.2500 BRL" in result

@patch('src.tools.finance_tools._fetch_usd_brl_timeseries', return_value=[])
def test_predict_usd_brl_trend_no_data(mock_fetch):
    result = predict_usd_brl_trend("previsão do dólar")
    assert "Não foi possível obter dados recentes" in result
