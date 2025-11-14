# Binance API 파라미터 중간 데이터 구조

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OrderParams:
    # Binance API 주문 파라미터
    symbol: str
    side: str  # BUY or SELL
    type: str  # LIMIT, MARKET, STOP_LOSS_LIMIT 등
    quantity: Optional[float] = None
    price: Optional[float] = None
    timeInForce: Optional[str] = None  # GTC, IOC, FOK
    stopPrice: Optional[float] = None


@dataclass(frozen=True)
class QueryParams:
    # 조회 요청 파라미터
    symbol: Optional[str] = None
    orderId: Optional[int] = None
    limit: Optional[int] = None
    startTime: Optional[int] = None
    endTime: Optional[int] = None


@dataclass(frozen=True)
class MarketDataParams:
    # 시장 데이터 조회 파라미터
    symbol: str
    interval: Optional[str] = None  # K선 간격
    limit: Optional[int] = None  # 조회 개수
