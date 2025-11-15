"""PriceDataRequest - 캔들 데이터 조회 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class PriceDataRequest(BaseRequest):
    """캔들 데이터(OHLCV) 조회를 요청한다.

    Note:
        거래 전략 실행 중 필요한 제한적/즉시적 캔들 조회에 사용된다.
        대량 히스토리 데이터 수집이나 백테스팅용 데이터 준비는
        별도 캔들 스토리지 시스템(financial-assets/candle)을 사용해야 한다.
    """

    address: StockAddress
    interval: str
    start: Optional[int] = None
    end: Optional[int] = None
