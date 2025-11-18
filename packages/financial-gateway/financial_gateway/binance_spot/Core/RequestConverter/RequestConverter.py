from typing import Dict, Any
from financial_gateway.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
    CloseOrderRequest,
    OrderCurrentStateRequest,
)


class RequestConverter:
    """
    Request 객체를 Binance API 파라미터로 변환
    Stateless 변환 로직
    """

    @staticmethod
    def _address_to_symbol(address) -> str:
        """StockAddress를 Binance 심볼 포맷으로 변환"""
        return f"{address.base}{address.quote}"

    @staticmethod
    def convert_limit_buy_order(request: LimitBuyOrderRequest) -> Dict[str, Any]:
        """지정가 매수 주문 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "side": "BUY",
            "type": "LIMIT",
            "quantity": str(request.volume),
            "price": str(request.price),
            "timeInForce": "GTX" if request.post_only else "GTC",
        }
        return params

    @staticmethod
    def convert_limit_sell_order(request: LimitSellOrderRequest) -> Dict[str, Any]:
        """지정가 매도 주문 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "side": "SELL",
            "type": "LIMIT",
            "quantity": str(request.volume),
            "price": str(request.price),
            "timeInForce": "GTX" if request.post_only else "GTC",
        }
        return params

    @staticmethod
    def convert_market_buy_order(request: MarketBuyOrderRequest) -> Dict[str, Any]:
        """시장가 매수 주문 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "side": "BUY",
            "type": "MARKET",
            "quantity": str(request.volume),
        }
        return params

    @staticmethod
    def convert_market_sell_order(request: MarketSellOrderRequest) -> Dict[str, Any]:
        """시장가 매도 주문 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "side": "SELL",
            "type": "MARKET",
            "quantity": str(request.volume),
        }
        return params

    @staticmethod
    def convert_cancel_order(request: CloseOrderRequest) -> Dict[str, Any]:
        """주문 취소 요청 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "orderId": int(request.order_id),
        }
        return params

    @staticmethod
    def convert_order_status_request(request: OrderCurrentStateRequest) -> Dict[str, Any]:
        """주문 상태 조회 요청 변환"""
        params = {
            "symbol": RequestConverter._address_to_symbol(request.address),
            "orderId": int(request.order_id),
        }
        return params
