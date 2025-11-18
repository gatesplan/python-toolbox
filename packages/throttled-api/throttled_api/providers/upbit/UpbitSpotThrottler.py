"""
Upbit Spot API Throttler

BaseThrottler를 상속하여 Upbit Spot API의 rate limit 관리
"""
import logging
from typing import Any, Literal
from ...core.BaseThrottler import BaseThrottler
from ...core.Pipeline import Pipeline
from ...core.window.FixedWindow import FixedWindow
from ...core.window.SlidingWindow import SlidingWindow
from .mixins import (
    QuotationMixin,
    AccountMixin,
    TradingMixin,
    DepositsMixin,
    WithdrawalsMixin,
)


logger = logging.getLogger(__name__)

EndpointCategory = Literal["QUOTATION", "EXCHANGE_ORDER", "EXCHANGE_NON_ORDER"]


class UpbitSpotThrottler(
    QuotationMixin,
    AccountMixin,
    TradingMixin,
    DepositsMixin,
    WithdrawalsMixin,
    BaseThrottler,
):
    """
    Upbit Spot API Throttler (Proxy 패턴 with Mixins)

    기존 Upbit 클라이언트를 감싸서 rate limit 관리.
    각 엔드포인트별 메서드를 제공하며, Mixin으로 구성됨.
    실제 HTTP 요청은 주입받은 client가 처리.

    Rate Limit 정책:
    - QUOTATION: 초당 10회, 분당 600회 (시세 조회)
    - EXCHANGE_ORDER: 초당 8회, 분당 200회 (주문 생성/취소)
    - EXCHANGE_NON_ORDER: 초당 30회, 분당 900회 (주문 외 요청)

    Usage:
        throttler = UpbitSpotThrottler(client)
        await throttler.get_ticker(markets=["KRW-BTC"])
        await throttler.create_order(market="KRW-BTC", side="bid", ord_type="limit", ...)
    """

    def __init__(
        self,
        client: Any,
        warning_threshold: float = 0.2,
    ):
        """
        Args:
            client: Upbit API 클라이언트 (upbit-client, pyupbit 등)
            warning_threshold: 서버와 로컬 사용량 차이가 이 비율 이상이면 경고 (0.0 ~ 1.0)
        """
        # Pipeline 구성 - 6개 Pipeline (카테고리별 초당/분당 제한)

        # 1. QUOTATION 초당 제한
        quotation_sec_pipeline = Pipeline(
            timeframe="QUOTATION_1S",
            window=SlidingWindow(limit=10, window_seconds=1, max_soft_delay=0.1),
            threshold=0.8,
        )

        # 2. QUOTATION 분당 제한
        quotation_min_pipeline = Pipeline(
            timeframe="QUOTATION_1M",
            window=FixedWindow(limit=600, window_seconds=60, max_soft_delay=0.3),
            threshold=0.8,
        )

        # 3. EXCHANGE_ORDER 초당 제한
        exchange_order_sec_pipeline = Pipeline(
            timeframe="EXCHANGE_ORDER_1S",
            window=SlidingWindow(limit=8, window_seconds=1, max_soft_delay=0.1),
            threshold=0.8,
        )

        # 4. EXCHANGE_ORDER 분당 제한
        exchange_order_min_pipeline = Pipeline(
            timeframe="EXCHANGE_ORDER_1M",
            window=FixedWindow(limit=200, window_seconds=60, max_soft_delay=0.3),
            threshold=0.8,
        )

        # 5. EXCHANGE_NON_ORDER 초당 제한
        exchange_non_order_sec_pipeline = Pipeline(
            timeframe="EXCHANGE_NON_ORDER_1S",
            window=SlidingWindow(limit=30, window_seconds=1, max_soft_delay=0.1),
            threshold=0.8,
        )

        # 6. EXCHANGE_NON_ORDER 분당 제한
        exchange_non_order_min_pipeline = Pipeline(
            timeframe="EXCHANGE_NON_ORDER_1M",
            window=FixedWindow(limit=900, window_seconds=60, max_soft_delay=0.3),
            threshold=0.8,
        )

        pipelines = [
            quotation_sec_pipeline,
            quotation_min_pipeline,
            exchange_order_sec_pipeline,
            exchange_order_min_pipeline,
            exchange_non_order_sec_pipeline,
            exchange_non_order_min_pipeline,
        ]

        super().__init__(pipelines=pipelines)

        self.client = client
        self.warning_threshold = warning_threshold

        # Pipeline 참조 저장 (카테고리별)
        self.quotation_pipelines = [quotation_sec_pipeline, quotation_min_pipeline]
        self.exchange_order_pipelines = [exchange_order_sec_pipeline, exchange_order_min_pipeline]
        self.exchange_non_order_pipelines = [
            exchange_non_order_sec_pipeline,
            exchange_non_order_min_pipeline,
        ]

    async def _check_and_wait(self, cost: int, category: EndpointCategory) -> None:
        """
        카테고리별 Pipeline에 대해 throttle 체크 및 대기

        Args:
            cost: 요청 소모량 (Upbit은 모두 1)
            category: 엔드포인트 카테고리
        """
        # 카테고리에 해당하는 Pipeline들만 체크
        if category == "QUOTATION":
            target_pipelines = self.quotation_pipelines
        elif category == "EXCHANGE_ORDER":
            target_pipelines = self.exchange_order_pipelines
        elif category == "EXCHANGE_NON_ORDER":
            target_pipelines = self.exchange_non_order_pipelines
        else:
            raise ValueError(f"Unknown category: {category}")

        # 해당 카테고리의 Pipeline들만 체크 및 대기
        async with self._lock:
            while True:
                # 모든 Pipeline이 통과할 수 있는지 체크
                can_proceed = all(
                    pipeline.window.can_send(cost) for pipeline in target_pipelines
                )

                if can_proceed:
                    # 모두 통과 가능하면 소비하고 진행
                    for pipeline in target_pipelines:
                        pipeline.consume(cost)
                    break

                # 하나라도 실패하면 가장 긴 대기 시간만큼 대기
                max_wait = max(
                    pipeline.window.wait_time(cost) for pipeline in target_pipelines
                )

                if max_wait > 0:
                    logger.debug(
                        f"[{category}] Rate limit approaching, waiting {max_wait:.2f}s"
                    )
                    # Lock 해제 후 대기
                    self._lock.release()
                    try:
                        await self._sleep(max_wait)
                    finally:
                        await self._lock.acquire()
