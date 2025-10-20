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
    """
    현물 거래 장부의 개별 거래 기록을 표현하는 불변 데이터 구조.

    SpotLedgerEntry는 하나의 거래가 장부에 미친 영향을 기록합니다.
    거래 시각, 원본 거래 정보, 자산/가치 변화량, 누적 포지션, 평균 진입가,
    실현 손익을 포함합니다.

    Attributes:
        timestamp (int): 거래 시각 (Unix timestamp)
        trade (SpotTrade): 원본 거래 객체
        asset_change (float): 자산 변화량 (양수: 증가, 음수: 감소)
        value_change (float): 가치 변화량 (양수: 증가, 음수: 감소)
        cumulative_asset (float): 이 거래 후 누적 자산 보유량
        cumulative_value (float): 이 거래 후 누적 가치 (투자금 누적)
        average_price (float): 이 거래 후 평균 진입가
        realized_pnl (Optional[float]): 실현 손익 (SELL 거래 시에만 발생)

    Examples:
        >>> from financial_assets.trade import SpotTrade, SpotSide
        >>> from financial_assets.pair import Pair
        >>> from financial_assets.token import Token
        >>> from financial_assets.stock_address import StockAddress
        >>>
        >>> stock_address = StockAddress(
        ...     archetype="crypto",
        ...     exchange="binance",
        ...     tradetype="spot",
        ...     base="btc",
        ...     quote="usdt",
        ...     timeframe="1d"
        ... )
        >>>
        >>> trade = SpotTrade(
        ...     stock_address=stock_address,
        ...     trade_id="trade-1",
        ...     fill_id="fill-1",
        ...     side=SpotSide.BUY,
        ...     pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
        ...     timestamp=1234567890
        ... )
        >>>
        >>> entry = SpotLedgerEntry(
        ...     timestamp=1234567890,
        ...     trade=trade,
        ...     asset_change=1.0,
        ...     value_change=-50000.0,
        ...     cumulative_asset=1.0,
        ...     cumulative_value=-50000.0,
        ...     average_price=50000.0,
        ...     realized_pnl=None
        ... )
        >>>
        >>> entry.timestamp
        1234567890
        >>> entry.asset_change
        1.0
        >>> entry.realized_pnl is None
        True
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
        """
        SpotLedgerEntry의 읽기 쉬운 문자열 표현을 반환합니다.

        Returns:
            str: 시각, 거래 방향, 변화량 정보를 포함한 문자열
        """
        pnl_str = f", PnL={self.realized_pnl:.2f}" if self.realized_pnl is not None else ""
        return (
            f"SpotLedgerEntry(ts={self.timestamp}, side={self.trade.side.name}, "
            f"asset_change={self.asset_change:.4f}, "
            f"cumulative={self.cumulative_asset:.4f}@{self.average_price:.2f}"
            f"{pnl_str})"
        )

    def __repr__(self) -> str:
        """
        SpotLedgerEntry의 상세한 문자열 표현을 반환합니다.

        Returns:
            str: 모든 필드 정보를 포함한 재생성 가능한 형식의 문자열
        """
        return (
            f"SpotLedgerEntry(timestamp={self.timestamp}, "
            f"trade={self.trade!r}, asset_change={self.asset_change}, "
            f"value_change={self.value_change}, "
            f"cumulative_asset={self.cumulative_asset}, "
            f"cumulative_value={self.cumulative_value}, "
            f"average_price={self.average_price}, "
            f"realized_pnl={self.realized_pnl})"
        )
