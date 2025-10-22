"""Spot ledger entry data structure.

This module provides the SpotLedgerEntry dataclass for representing individual
trade records in a spot trading ledger.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from ..trade import SpotTrade


@dataclass(frozen=True)
class SpotLedgerEntry:
    """단일 거래 기록 엔트리 (불변 데이터).
    거래와 그 시점의 포지션 상태를 저장합니다.
    """

    timestamp: int
    trade: SpotTrade
    asset_change: float
    value_change: float
    cumulative_asset: float
    cumulative_value: float
    average_price: float
    realized_pnl: Optional[float] = None

    def __str__(self) -> str:
        """읽기 쉬운 문자열 표현 반환."""
        pnl_str = f", PnL={self.realized_pnl:.2f}" if self.realized_pnl is not None else ""
        return (
            f"SpotLedgerEntry(ts={self.timestamp}, side={self.trade.side.name}, "
            f"asset_change={self.asset_change:.4f}, "
            f"cumulative={self.cumulative_asset:.4f}@{self.average_price:.2f}"
            f"{pnl_str})"
        )

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        return (
            f"SpotLedgerEntry(timestamp={self.timestamp}, "
            f"trade={self.trade!r}, asset_change={self.asset_change}, "
            f"value_change={self.value_change}, "
            f"cumulative_asset={self.cumulative_asset}, "
            f"cumulative_value={self.cumulative_value}, "
            f"average_price={self.average_price}, "
            f"realized_pnl={self.realized_pnl})"
        )
