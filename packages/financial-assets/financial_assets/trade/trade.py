"""Trade data structure.

This module provides the Trade dataclass for representing completed trade records.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .trade_side import TradeSide
from ..pair import Pair
from ..stock_address import StockAddress
from ..token import Token


@dataclass(frozen=True)
class Trade:
    """
    체결 완료된 거래를 표현하는 불변 데이터 구조.

    Trade는 거래 시뮬레이션이나 실제 거래소 API에서 발생한 체결 정보를
    표준화된 형식으로 캡슐화합니다. 생성 후 수정이 불가능한 불변 객체입니다.

    Attributes:
        stock_address (StockAddress): 거래가 발생한 시장/거래소 정보
        trade_id (str): 거래 식별자
        fill_id (str): 체결 식별자
        side (TradeSide): 거래 방향 (BUY, SELL, LONG, SHORT)
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
        >>> trade = Trade(
        ...     stock_address=stock_address,
        ...     trade_id="trade-123",
        ...     fill_id="fill-456",
        ...     side=TradeSide.BUY,
        ...     pair=pair,
        ...     timestamp=1234567890
        ... )
        >>> trade.trade_id
        'trade-123'
        >>> trade.side
        <TradeSide.BUY: 'buy'>
        >>> trade.pair.get_asset()
        1.5
    """

    stock_address: StockAddress
    trade_id: str
    fill_id: str
    side: TradeSide
    pair: Pair
    timestamp: int
    fee: Optional[Token] = None

    def __str__(self) -> str:
        """
        Trade의 읽기 쉬운 문자열 표현을 반환합니다.

        Returns:
            str: 거래 ID, 방향, 자산 쌍 정보를 포함한 문자열
        """
        return (
            f"Trade(id={self.trade_id}, side={self.side.name}, "
            f"pair={self.pair}, timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        """
        Trade의 상세한 문자열 표현을 반환합니다.

        Returns:
            str: 모든 필드 정보를 포함한 재생성 가능한 형식의 문자열
        """
        return (
            f"Trade(stock_address={self.stock_address!r}, "
            f"trade_id={self.trade_id!r}, fill_id={self.fill_id!r}, "
            f"side={self.side!r}, pair={self.pair!r}, "
            f"timestamp={self.timestamp}, fee={self.fee!r})"
        )
