"""
Binance Spot API Throttler

BaseThrottler를 상속하여 Binance Spot API의 rate limit 관리
"""
from typing import Any, Dict, Optional, Callable
from simple_logger import init_logging, func_logging, logger
from ...core.BaseThrottler import BaseThrottler
from ...core.Pipeline import Pipeline
from ...core.window.FixedWindow import FixedWindow
from . import endpoints
from .exceptions import UnknownEndpointError
from .mixins import (
    GeneralMixin,
    MarketDataMixin,
    TradingMixin,
    AccountMixin,
    UserDataStreamMixin,
)


class BinanceSpotThrottler(
    GeneralMixin,
    MarketDataMixin,
    TradingMixin,
    AccountMixin,
    UserDataStreamMixin,
    BaseThrottler,
):
    """
    Binance Spot API Throttler (Proxy 패턴 with Mixins)

    기존 Binance 클라이언트를 감싸서 rate limit 관리.
    각 엔드포인트별 메서드를 제공하며, Mixin으로 구성됨.
    실제 HTTP 요청은 주입받은 client가 처리.

    Usage:
        throttler = BinanceSpotThrottler(client)
        await throttler.ping()
        await throttler.get_ticker_price(symbol="BTCUSDT")
        await throttler.create_order(symbol="BTCUSDT", side="BUY", type="LIMIT", ...)
    """

    @init_logging(level="INFO")
    def __init__(
        self,
        client: Any,
        threshold: float = 0.5,
        max_soft_delay: float = 1.0,
    ):
        """
        Args:
            client: Binance API 클라이언트
            threshold: soft limiting 시작 임계값 (0.0~1.0), 기본 0.5
            max_soft_delay: soft limiting 최대 대기 시간 (초), 기본 1.0
        """
        # REQUEST_WEIGHT Pipeline: 1분당 6000
        weight_pipeline = Pipeline(
            timeframe="REQUEST_WEIGHT_1M",
            window=FixedWindow(
                limit=6000,
                window_seconds=60,
                max_soft_delay=max_soft_delay,
                threshold=threshold,
            ),
            threshold=threshold,
        )

        super().__init__(pipelines=[weight_pipeline])

        # ORDERS Pipelines (주문 전용 제한)
        self.order_pipelines = [
            Pipeline(
                timeframe="ORDERS_10S",
                window=FixedWindow(
                    limit=100,
                    window_seconds=10,
                    max_soft_delay=max_soft_delay,
                    threshold=threshold,
                ),
                threshold=threshold,
            ),
            Pipeline(
                timeframe="ORDERS_1D",
                window=FixedWindow(
                    limit=200000,
                    window_seconds=86400,
                    max_soft_delay=max_soft_delay,
                    threshold=threshold,
                ),
                threshold=threshold,
            ),
        ]

        # Order pipelines에 이벤트 리스너 연결
        for pipeline in self.order_pipelines:
            pipeline.add_listener(self._on_pipeline_event)

        self.client = client
        self.weight_pipeline = weight_pipeline
        self._order_lock = __import__('asyncio').Lock()

    async def _check_orders(self, order_count: int = 1) -> None:
        """
        주문 제한 체크 및 대기

        ORDERS 제한만 체크 (REQUEST_WEIGHT는 별도로 체크)

        Args:
            order_count: 주문 개수 (기본 1)
        """
        import asyncio
        while True:
            # 모든 ORDERS Pipeline의 대기 시간 계산
            wait_times = [p.wait_time(order_count) for p in self.order_pipelines]
            max_wait = max(wait_times) if wait_times else 0.0

            # 대기가 필요하면 sleep
            if max_wait > 0:
                logger.debug(f"Order rate limit 대기: {max_wait:.3f}초 (count={order_count})")
                await asyncio.sleep(max_wait)
                continue

            # 대기 불필요 → consume 시도
            async with self._order_lock:
                # 모든 Pipeline이 통과하는지 재확인
                can_send_all = all(p.can_send(order_count) for p in self.order_pipelines)

                if can_send_all:
                    # 모두 통과 → 모든 Pipeline에 차감
                    for pipeline in self.order_pipelines:
                        pipeline.consume(order_count)
                    return
                # can_send 실패 시 다음 루프에서 재계산
