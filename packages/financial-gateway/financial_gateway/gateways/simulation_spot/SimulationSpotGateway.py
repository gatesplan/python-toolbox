# SimulationSpotGateway - Simulation Spot Gateway Director (SDW 패턴)

# standard library
from typing import Dict, Type

# third party
from simple_logger import init_logging, logger

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


class SimulationSpotGateway(SpotMarketGatewayBase):
    # Simulation Spot Gateway Director
    # Exchange를 공유 리소스로 보유하며, Request 타입에 따라 적절한 Worker로 라우팅

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

        # Worker 인스턴스 생성
        self._cancel_order_worker = CancelOrderWorker(exchange)
        self._create_order_worker = CreateOrderWorker(exchange)
        self._modify_or_replace_order_worker = ModifyOrReplaceOrderWorker(exchange)
        self._see_available_markets_worker = SeeAvailableMarketsWorker(exchange)
        self._see_balance_worker = SeeBalanceWorker(exchange)
        self._see_candles_worker = SeeCandlesWorker(exchange)
        self._see_holdings_worker = SeeHoldingsWorker(exchange)
        self._see_open_orders_worker = SeeOpenOrdersWorker(exchange)
        self._see_order_worker = SeeOrderWorker(exchange)
        self._see_orderbook_worker = SeeOrderbookWorker(exchange)
        self._see_server_time_worker = SeeServerTimeWorker(exchange)
        self._see_ticker_worker = SeeTickerWorker(exchange)
        self._see_trades_worker = SeeTradesWorker(exchange)

        # Request 타입 → Worker 매핑 딕셔너리
        self._workers: Dict[Type[BaseRequest], object] = {
            CancelOrderRequest: self._cancel_order_worker,
            CreateOrderRequest: self._create_order_worker,
            ModifyOrReplaceOrderRequest: self._modify_or_replace_order_worker,
            SeeAvailableMarketsRequest: self._see_available_markets_worker,
            SeeBalanceRequest: self._see_balance_worker,
            SeeCandlesRequest: self._see_candles_worker,
            SeeHoldingsRequest: self._see_holdings_worker,
            SeeOpenOrdersRequest: self._see_open_orders_worker,
            SeeOrderRequest: self._see_order_worker,
            SeeOrderbookRequest: self._see_orderbook_worker,
            SeeServerTimeRequest: self._see_server_time_worker,
            SeeTickerRequest: self._see_ticker_worker,
            SeeTradesRequest: self._see_trades_worker,
        }

    @property
    def gateway_name(self) -> str:
        return "simulation_spot"

    @property
    def is_realworld_gateway(self) -> bool:
        return False

    async def execute(self, request: BaseRequest) -> BaseResponse:
        # Request 타입에 따라 적절한 Worker로 라우팅
        worker = self._workers.get(type(request))

        if worker is None:
            logger.error(f"Unsupported request type: {type(request).__name__}")
            raise ValueError(
                f"Unsupported request type: {type(request).__name__}"
            )

        logger.debug(f"Routing {type(request).__name__} to {type(worker).__name__}")
        # Simulation Worker는 동기 함수이므로 await 없이 호출
        return worker.execute(request)
