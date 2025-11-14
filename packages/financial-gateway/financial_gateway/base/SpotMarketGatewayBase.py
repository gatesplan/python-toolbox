# Spot 거래의 통일된 인터페이스를 정의하는 추상 클래스

from abc import ABC, abstractmethod
from financial_gateway.base.BaseGateway import BaseGateway


class SpotMarketGatewayBase(BaseGateway, ABC):
    # 모든 Spot Gateway 구현체가 구현해야 하는 인터페이스

    @abstractmethod
    def request_limit_buy_order(self, request):
        # LimitBuyOrderRequest -> OpenSpotOrderResponse
        pass

    @abstractmethod
    def request_limit_sell_order(self, request):
        # LimitSellOrderRequest -> OpenSpotOrderResponse
        pass

    @abstractmethod
    def request_market_buy_order(self, request):
        # MarketBuyOrderRequest -> OpenSpotOrderResponse
        pass

    @abstractmethod
    def request_market_sell_order(self, request):
        # MarketSellOrderRequest -> OpenSpotOrderResponse
        pass

    @abstractmethod
    def request_cancel_order(self, request):
        # CancelOrderRequest -> CancelOrderResponse
        pass

    @abstractmethod
    def request_order_status(self, request):
        # OrderStatusRequest -> OrderStatusResponse
        pass

    @abstractmethod
    def request_current_balance(self, request):
        # BalanceRequest -> BalanceResponse
        pass

    @abstractmethod
    def request_trade_history(self, request):
        # TradeHistoryRequest -> TradeHistoryResponse
        pass

    @abstractmethod
    def request_ticker(self, request):
        # TickerRequest -> TickerResponse
        pass

    @abstractmethod
    def request_orderbook(self, request):
        # OrderbookRequest -> OrderbookResponse
        pass

    @abstractmethod
    def request_candles(self, request):
        # CandleRequest -> CandleResponse
        pass

    @abstractmethod
    def request_available_markets(self, request):
        # MarketListRequest -> MarketListResponse
        pass

    @abstractmethod
    def request_server_time(self):
        # ServerTimeResponse
        pass
