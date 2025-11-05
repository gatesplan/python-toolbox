"""Futures trade data structure.

This module provides the FuturesTrade dataclass for representing completed futures trade records.
Futures trading involves leveraged positions with realized PnL tracking.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .trade import Trade
from ..token import Token


@dataclass(frozen=True)
class FuturesTrade(Trade):
    """체결 완료된 선물 거래 (불변 데이터 구조).
    포지션 개념과 실현손익을 포함하는 선물 거래의 체결 정보를 표준화합니다.
    """

    realized_pnl: Optional[Token] = None

    def __str__(self) -> str:
        """거래 정보의 읽기 쉬운 문자열 표현."""
        return (
            f"FuturesTrade(id={self.trade_id}, side={self.side.name}, "
            f"pair={self.pair}, pnl={self.realized_pnl}, timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        """재생성 가능한 상세 문자열 표현."""
        return (
            f"FuturesTrade(trade_id={self.trade_id!r}, "
            f"order={self.order!r}, "
            f"pair={self.pair!r}, "
            f"timestamp={self.timestamp}, fee={self.fee!r}, "
            f"realized_pnl={self.realized_pnl!r})"
        )
