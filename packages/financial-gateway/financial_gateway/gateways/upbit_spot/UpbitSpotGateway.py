# standard library
from typing import Dict, Type

# third party
from simple_logger import init_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler

# local (in same package)
from ..base import SpotMarketGatewayBase
from ...structures import (
    BaseRequest,
    BaseResponse,
    CancelOrderRequest,
    CreateOrderRequest,
    ModifyOrReplaceOrderRequest,
    SeeAvailableMarketsRequest,
    SeeBalanceRequest,
    SeeCandlesRequest,
    SeeHoldingsRequest,
    SeeOpenOrdersRequest,
    SeeOrderRequest,
    SeeOrderbookRequest,
    SeeServerTimeRequest,
    SeeTickerRequest,
    SeeTradesRequest,
)
from .workers import (
    CancelOrderWorker,
    CreateOrderWorker,
    ModifyOrReplaceOrderWorker,
    SeeAvailableMarketsWorker,
    SeeBalanceWorker,
    SeeCandlesWorker,
    SeeHoldingsWorker,
    SeeOpenOrdersWorker,
    SeeOrderWorker,
    SeeOrderbookWorker,
    SeeServerTimeWorker,
    SeeTickerWorker,
    SeeTradesWorker,
)


class UpbitSpotGateway(SpotMarketGatewayBase):
    # Upbit Spot Gateway Director (SDW 패턴)
    # Throttler를 공유 리소스로 보유하며, Request 타입에 따라 적절한 Worker로 라우팅
    # Upbit 특징:
    # - 기본 quote currency: KRW
    # - 평단가 직접 제공 (avg_buy_price)
    # - 주문 타입: bid(매수), ask(매도)
    # - ord_type: limit(지정가), price(시장가 매수), market(시장가 매도)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

        # Worker 인스턴스 생성
        self._create_order_worker = CreateOrderWorker(throttler)
        self._cancel_order_worker = CancelOrderWorker(throttler)
        self._modify_or_replace_order_worker = ModifyOrReplaceOrderWorker(throttler)
        self._see_order_worker = SeeOrderWorker(throttler)
        self._see_open_orders_worker = SeeOpenOrdersWorker(throttler)
        self._see_holdings_worker = SeeHoldingsWorker(throttler)
        self._see_balance_worker = SeeBalanceWorker(throttler)
        self._see_available_markets_worker = SeeAvailableMarketsWorker(throttler)
        self._see_ticker_worker = SeeTickerWorker(throttler)
        self._see_orderbook_worker = SeeOrderbookWorker(throttler)
        self._see_trades_worker = SeeTradesWorker(throttler)
        self._see_candles_worker = SeeCandlesWorker(throttler)
        self._see_server_time_worker = SeeServerTimeWorker(throttler)

        # Request 타입 → Worker 매핑 딕셔너리
        self._workers: Dict[Type[BaseRequest], object] = {
            CreateOrderRequest: self._create_order_worker,
            CancelOrderRequest: self._cancel_order_worker,
            ModifyOrReplaceOrderRequest: self._modify_or_replace_order_worker,
            SeeOrderRequest: self._see_order_worker,
            SeeOpenOrdersRequest: self._see_open_orders_worker,
            SeeHoldingsRequest: self._see_holdings_worker,
            SeeBalanceRequest: self._see_balance_worker,
            SeeAvailableMarketsRequest: self._see_available_markets_worker,
            SeeTickerRequest: self._see_ticker_worker,
            SeeOrderbookRequest: self._see_orderbook_worker,
            SeeTradesRequest: self._see_trades_worker,
            SeeCandlesRequest: self._see_candles_worker,
            SeeServerTimeRequest: self._see_server_time_worker,
        }

    @property
    def gateway_name(self) -> str:
        return "upbit_spot"

    @property
    def is_realworld_gateway(self) -> bool:
        return True

    async def execute(self, request: BaseRequest) -> BaseResponse:
        """Request 타입에 따라 적절한 Worker로 라우팅"""
        worker = self._workers.get(type(request))

        if worker is None:
            logger.error(f"Unsupported request type: {type(request).__name__}")
            raise ValueError(
                f"Unsupported request type: {type(request).__name__}"
            )

        logger.debug(f"Routing {type(request).__name__} to {type(worker).__name__}")
        return await worker.execute(request)
