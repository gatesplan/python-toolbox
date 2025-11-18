"""
Binance Spot API Throttler

BaseThrottler를 상속하여 Binance Spot API의 rate limit 관리
"""
import logging
from typing import Any, Dict, Optional, Callable
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


logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        client: Any,
        warning_threshold: float = 0.2,
        enable_raw_requests_limit: bool = False,
        allow_unknown_endpoints: bool = False,
    ):
        """
        Args:
            client: Binance API 클라이언트 (python-binance, binance-connector-python 등)
            warning_threshold: 서버와 로컬 weight 차이가 이 비율 이상이면 경고 (0.0 ~ 1.0)
            enable_raw_requests_limit: RAW_REQUESTS 제한 활성화 (선택, 보수적)
            allow_unknown_endpoints: 알 수 없는 엔드포인트 허용 (weight=1로 처리), 기본 False
        """
        # Pipeline 구성 - REQUEST_WEIGHT만 BaseThrottler에 전달
        # ORDERS Pipeline은 별도로 관리 (주문 건수는 weight와 다르게 처리)
        weight_pipeline = Pipeline(
            timeframe="REQUEST_WEIGHT_1M",
            window=FixedWindow(limit=6000, window_seconds=60, max_soft_delay=0.3),
            threshold=0.8,  # 80% 사용 시 경고
        )

        pipelines = [weight_pipeline]

        if enable_raw_requests_limit:
            # RAW_REQUESTS: 5분당 61000 (선택적)
            pipelines.append(
                Pipeline(
                    timeframe="RAW_REQUESTS_5M",
                    window=FixedWindow(limit=61000, window_seconds=300, max_soft_delay=0.5),
                    threshold=0.8,
                )
            )

        super().__init__(pipelines=pipelines)

        self.client = client
        self.warning_threshold = warning_threshold
        self.allow_unknown_endpoints = allow_unknown_endpoints
        self.weight_pipeline = weight_pipeline  # REQUEST_WEIGHT_1M
