"""
BinanceSpotGateway
Binance Spot 거래소 API와 통신하는 Gateway Controller
"""
from simple_logger import init_logging, func_logging, logger
from financial_gateway.binance_spot.Core.Service.OrderRequestService import OrderRequestService
from financial_gateway.binance_spot.Core.Service.MarketDataService import MarketDataService
from financial_gateway.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
    CloseOrderRequest,
    OrderCurrentStateRequest,
    TickerRequest,
    OrderbookRequest,
    CurrentBalanceRequest,
)
from financial_gateway.response import (
    OpenSpotOrderResponse,
    CloseLimitOrderResponse,
    OrderCurrentStateResponse,
    TickerResponse,
    OrderbookResponse,
    CurrentBalanceResponse,
)


class BinanceSpotGateway:
    """
    Binance Spot Gateway
    Service 계층을 조합하여 Binance Spot 거래소와의 통합 인터페이스 제공
    """

    gateway_name: str = "binance"
    is_realworld_gateway: bool = True

    @init_logging(level="INFO")
    def __init__(self):
        """Gateway 초기화"""
        self._order_service = OrderRequestService()
        self._market_service = MarketDataService()
        logger.debug("BinanceSpotGateway 초기화 완료")

    # ====================
    # 주문 관리 메서드
    # ====================

    @func_logging(level="INFO")
    async def request_limit_buy_order(self, request: LimitBuyOrderRequest) -> OpenSpotOrderResponse:
        """지정가 매수 주문 요청"""
        return await self._order_service.limit_buy(request)

    @func_logging(level="INFO")
    async def request_limit_sell_order(self, request: LimitSellOrderRequest) -> OpenSpotOrderResponse:
        """지정가 매도 주문 요청"""
        return await self._order_service.limit_sell(request)

    @func_logging(level="INFO")
    async def request_market_buy_order(self, request: MarketBuyOrderRequest) -> OpenSpotOrderResponse:
        """시장가 매수 주문 요청"""
        return await self._order_service.market_buy(request)

    @func_logging(level="INFO")
    async def request_market_sell_order(self, request: MarketSellOrderRequest) -> OpenSpotOrderResponse:
        """시장가 매도 주문 요청"""
        return await self._order_service.market_sell(request)

    @func_logging(level="INFO")
    async def request_cancel_order(self, request: CloseOrderRequest) -> CloseLimitOrderResponse:
        """주문 취소 요청"""
        return await self._order_service.cancel_order(request)

    @func_logging(level="INFO")
    async def request_order_status(self, request: OrderCurrentStateRequest) -> OrderCurrentStateResponse:
        """주문 상태 조회"""
        return await self._order_service.get_order_status(request)

    # ====================
    # 계정 정보 메서드
    # ====================

    @func_logging(level="INFO")
    async def request_current_balance(self, request: CurrentBalanceRequest) -> CurrentBalanceResponse:
        """현재 잔고 조회"""
        return await self._market_service.get_balance(request)

    # ====================
    # 시장 데이터 메서드
    # ====================

    @func_logging(level="INFO")
    async def request_ticker(self, request: TickerRequest) -> TickerResponse:
        """시세 정보 조회"""
        return await self._market_service.get_ticker(request)

    @func_logging(level="INFO")
    async def request_orderbook(self, request: OrderbookRequest) -> OrderbookResponse:
        """호가 정보 조회"""
        return await self._market_service.get_orderbook(request)
