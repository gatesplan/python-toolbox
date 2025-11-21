"""Market information data structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.symbol import Symbol
from financial_assets.constants import MarketStatus


@dataclass
class MarketInfo:
    """거래 가능 마켓 정보

    Attributes:
        symbol: 거래쌍 (예: Symbol("BTC/USDT"))
        status: 거래 상태 (None이면 UNKNOWN, Upbit은 항상 None)
        min_trade_value_size: 최소 주문금액 (quote currency 기준, 예: 10 USDT)
        min_trade_asset_size: 최소 주문수량 (base currency 기준, 예: 0.001 BTC)
        min_value_tick_size: 가격 호가 단위 (quote currency, 예: 0.01 USDT)
        min_asset_tick_size: 수량 호가 단위 (base currency, 예: 0.00000001 BTC)
    """
    symbol: Symbol
    status: Optional[MarketStatus] = None

    # 거래 규칙
    min_trade_value_size: Optional[float] = None    # 최소 주문금액 (quote)
    min_trade_asset_size: Optional[float] = None    # 최소 주문수량 (base)
    min_value_tick_size: Optional[float] = None     # 가격 호가 단위 (quote)
    min_asset_tick_size: Optional[float] = None     # 수량 호가 단위 (base)
