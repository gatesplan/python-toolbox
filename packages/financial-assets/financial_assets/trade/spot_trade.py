"""Spot trade data structure.

This module provides the SpotTrade dataclass for representing completed spot trade records.
Spot trading involves immediate exchange of assets (buy/sell).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from ..constants import Side
from ..pair import Pair
from ..stock_address import StockAddress
from ..token import Token


@dataclass(frozen=True)
class SpotTrade:
    """체결 완료된 현물 거래 (불변 데이터 구조).
    거래 시뮬레이션이나 실제 거래소 API의 체결 정보를 표준화합니다.
    """

    stock_address: StockAddress
    trade_id: str
    fill_id: str
    side: Side
    pair: Pair
    timestamp: int
    fee: Optional[Token] = None

    def __str__(self) -> str:
        """거래 정보의 읽기 쉬운 문자열 표현."""
        return (
            f"SpotTrade(id={self.trade_id}, side={self.side.name}, "
            f"pair={self.pair}, timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        """재생성 가능한 상세 문자열 표현."""
        return (
            f"SpotTrade(stock_address={self.stock_address!r}, "
            f"trade_id={self.trade_id!r}, fill_id={self.fill_id!r}, "
            f"side={self.side!r}, pair={self.pair!r}, "
            f"timestamp={self.timestamp}, fee={self.fee!r})"
        )
