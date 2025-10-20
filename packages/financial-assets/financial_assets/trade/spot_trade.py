"""Spot trade data structure.

This module provides the SpotTrade dataclass for representing completed spot trade records.
Spot trading involves immediate exchange of assets (buy/sell).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .spot_side import SpotSide
from ..pair import Pair
from ..stock_address import StockAddress
from ..token import Token


@dataclass(frozen=True)
class SpotTrade:
    """
    체결 완료된 현물 거래를 표현하는 불변 데이터 구조.

    SpotTrade는 현물 거래 시뮬레이션이나 실제 거래소 API에서 발생한 체결 정보를
    표준화된 형식으로 캡슐화합니다. 생성 후 수정이 불가능한 불변 객체입니다.

    현물 거래는 자산의 즉시 교환을 의미하며, 레버리지나 포지션 개념이 없습니다.
    선물 거래는 FuturesTrade를 사용하세요.

    Attributes:
        stock_address (StockAddress): 거래가 발생한 시장/거래소 정보
        trade_id (str): 거래 식별자
        fill_id (str): 체결 식별자
        side (SpotSide): 거래 방향 (BUY, SELL)
        pair (Pair): 거래된 자산 쌍 (수량, 가격, 평균 포함)
        timestamp (int): 거래 발생 시각 (Unix timestamp)
        fee (Token | None): 거래 수수료 (선택적, 기본값 None)

    Examples:
        >>> from financial_assets.token import Token
        >>> stock_address = StockAddress(
        ...     archetype="crypto",
        ...     exchange="binance",
        ...     tradetype="spot",
        ...     base="btc",
        ...     quote="usd",
        ...     timeframe="1d"
        ... )
        >>> pair = Pair(
        ...     asset=Token("BTC", 1.5),
        ...     value=Token("USD", 75000.0)
        ... )
        >>> trade = SpotTrade(
        ...     stock_address=stock_address,
        ...     trade_id="trade-123",
        ...     fill_id="fill-456",
        ...     side=SpotSide.BUY,
        ...     pair=pair,
        ...     timestamp=1234567890
        ... )
        >>> trade.trade_id
        'trade-123'
        >>> trade.side
        <SpotSide.BUY: 'buy'>
        >>> trade.pair.get_asset()
        1.5
    """

    stock_address: StockAddress
    trade_id: str
    fill_id: str
    side: SpotSide
    pair: Pair
    timestamp: int
    fee: Optional[Token] = None

    def __str__(self) -> str:
        """
        SpotTrade의 읽기 쉬운 문자열 표현을 반환합니다.

        Returns:
            str: 거래 ID, 방향, 자산 쌍 정보를 포함한 문자열
        """
        return (
            f"SpotTrade(id={self.trade_id}, side={self.side.name}, "
            f"pair={self.pair}, timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        """
        SpotTrade의 상세한 문자열 표현을 반환합니다.

        Returns:
            str: 모든 필드 정보를 포함한 재생성 가능한 형식의 문자열
        """
        return (
            f"SpotTrade(stock_address={self.stock_address!r}, "
            f"trade_id={self.trade_id!r}, fill_id={self.fill_id!r}, "
            f"side={self.side!r}, pair={self.pair!r}, "
            f"timestamp={self.timestamp}, fee={self.fee!r})"
        )
