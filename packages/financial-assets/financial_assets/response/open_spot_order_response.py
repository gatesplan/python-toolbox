"""OpenSpotOrderResponse - Spot 주문 생성 응답."""

from dataclasses import dataclass, field
from typing import Optional

from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade

from .base_response import BaseResponse


@dataclass
class OpenSpotOrderResponse(BaseResponse):
    """Spot 주문 생성 요청에 대한 통합 응답.

    모든 Spot 주문 타입(Limit, Market, StopLimit, StopMarket)에 사용된다.
    """

    # === 공통 검증 오류 ===
    is_insufficient_balance: bool = False
    is_min_notional_error: bool = False
    is_max_notional_error: bool = False
    is_quantity_step_size_error: bool = False
    is_market_suspended: bool = False
    is_invalid_market: bool = False

    # === 지정가 주문 관련 ===
    is_price_tick_size_error: bool = False
    is_post_only_rejected: bool = False

    # === 시장가 주문 관련 ===
    is_no_liquidity: bool = False

    # === TIF 관련 ===
    is_ioc_partially_cancelled: bool = False
    is_fok_rejected: bool = False

    # === Stop 주문 관련 ===
    is_stop_trigger_invalid: bool = False
    is_stop_price_too_close: bool = False

    # === 결과 데이터 ===
    order: Optional[SpotOrder] = None
    trades: list[SpotTrade] = field(default_factory=list)
