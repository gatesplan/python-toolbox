"""Spot trade data structure.

This module provides the SpotTrade dataclass for representing completed spot trade records.
Spot trading involves immediate exchange of assets (buy/sell).
"""

from __future__ import annotations
from dataclasses import dataclass

from .trade import Trade


@dataclass(frozen=True)
class SpotTrade(Trade):
    """체결 완료된 현물 거래 (불변 데이터 구조).
    거래 시뮬레이션이나 실제 거래소 API의 체결 정보를 표준화합니다.
    """

    def __str__(self) -> str:
        """거래 정보의 읽기 쉬운 문자열 표현."""
        return (
            f"SpotTrade(id={self.trade_id}, side={self.side.name}, "
            f"pair={self.pair}, timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        """재생성 가능한 상세 문자열 표현."""
        return (
            f"SpotTrade(trade_id={self.trade_id!r}, "
            f"order={self.order!r}, "
            f"pair={self.pair!r}, "
            f"timestamp={self.timestamp}, fee={self.fee!r})"
        )
