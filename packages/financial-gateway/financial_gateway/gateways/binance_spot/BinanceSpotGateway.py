from typing import Dict, Type
from simple_logger import init_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.gateways.base import SpotMarketGatewayBase
from financial_gateway.structures.base import BaseRequest, BaseResponse
from financial_gateway.structures.create_order import CreateOrderRequest
from financial_gateway.structures.cancel_order import CancelOrderRequest
from financial_gateway.structures.modify_or_replace_order import ModifyOrReplaceOrderRequest
from financial_gateway.structures.see_order import SeeOrderRequest
from financial_gateway.structures.see_open_orders import SeeOpenOrdersRequest
from financial_gateway.structures.see_holdings import SeeHoldingsRequest
from financial_gateway.structures.see_balance import SeeBalanceRequest
from financial_gateway.structures.see_available_markets import SeeAvailableMarketsRequest
from financial_gateway.structures.see_ticker import SeeTickerRequest
from financial_gateway.structures.see_orderbook import SeeOrderbookRequest
from financial_gateway.structures.see_trades import SeeTradesRequest
from financial_gateway.structures.see_candles import SeeCandlesRequest
from financial_gateway.structures.see_server_time import SeeServerTimeRequest


class BinanceSpotGateway(SpotMarketGatewayBase):
    """Binance Spot Gateway Director (SDW 패턴)

    Throttler를 공유 리소스로 보유하며, Request 타입에 따라 적절한 Worker로 라우팅.
    """

    @init_logging(level="INFO", log_params=True)
    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

        # Workers 생성 (지연 임포트로 순환 참조 방지)
        from .workers.CreateOrderWorker import CreateOrderWorker
        from .workers.CancelOrderWorker import CancelOrderWorker
        from .workers.ModifyOrReplaceOrderWorker import ModifyOrReplaceOrderWorker
        from .workers.SeeOrderWorker import SeeOrderWorker
        from .workers.SeeOpenOrdersWorker import SeeOpenOrdersWorker
        from .workers.SeeHoldingsWorker import SeeHoldingsWorker
        from .workers.SeeBalanceWorker import SeeBalanceWorker
        from .workers.SeeAvailableMarketsWorker import SeeAvailableMarketsWorker
        from .workers.SeeTickerWorker import SeeTickerWorker
        from .workers.SeeOrderbookWorker import SeeOrderbookWorker
        from .workers.SeeTradesWorker import SeeTradesWorker
        from .workers.SeeCandlesWorker import SeeCandlesWorker
        from .workers.SeeServerTimeWorker import SeeServerTimeWorker

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
        return "binance_spot"

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
