from .balance import balance_tool
from .investment import investment_tool
from .transfer import transfer_tool
from .fetch_data import fetch_data_tool
from .trend import trend_tool, classify_usd_brl_trend_from_series

finance_tools = [
    balance_tool,
    investment_tool,
    transfer_tool,
    fetch_data_tool,
    trend_tool,
]

__all__ = [
    "finance_tools",
    "classify_usd_brl_trend_from_series",
]
