"""OrderbookResponse - 호가창 조회 응답."""

from dataclasses import dataclass, field

from .base_response import BaseResponse


@dataclass
class OrderbookResponse(BaseResponse):
    """호가창 조회 요청에 대한 응답.

    현재 매수/매도 호가 스냅샷을 제공한다.
    """

    # 고유 상태 플래그
    is_invalid_market: bool = False

    # 결과 데이터
    symbol: str = ""
    bids: list[tuple[float, float]] = field(default_factory=list)  # [(가격, 수량), ...] 가격 높은 순
    asks: list[tuple[float, float]] = field(default_factory=list)  # [(가격, 수량), ...] 가격 낮은 순
    timestamp: int = 0  # 스냅샷 생성 시각
