from typing import Dict, Any, Optional
from financial_gateway.response import (
    OpenSpotOrderResponse,
    OrderCurrentStateResponse,
    CurrentBalanceResponse,
    TickerResponse,
    OrderbookResponse,
)
from financial_assets.order import SpotOrder
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress
from financial_assets.constants import Side, OrderType, OrderStatus, TimeInForce
import time


class ResponseParser:
    """
    Binance API 응답을 Response 객체로 파싱
    Stateless 파싱 로직
    """

    @staticmethod
    def _parse_symbol_to_stock_address(symbol: str) -> StockAddress:
        """Binance 심볼을 StockAddress로 변환 (간단한 파싱)"""
        # BTCUSDT -> base=BTC, quote=USDT
        # 간단한 휴리스틱: 뒤 3~4자리가 USDT, BTC, ETH, BNB 등인 경우
        common_quotes = ["USDT", "BUSD", "USDC", "BTC", "ETH", "BNB"]

        for quote in common_quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return StockAddress(
                    archetype="candle",
                    exchange="binance",
                    tradetype="spot",
                    base=base,
                    quote=quote,
                    timeframe="1m",
                )

        # 매칭 실패 시 기본값 (개선 필요)
        return StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base=symbol[:-3] if len(symbol) > 3 else symbol,
            quote=symbol[-3:] if len(symbol) > 3 else "USD",
            timeframe="1m",
        )

    @staticmethod
    def _parse_side(side_str: str) -> Side:
        """Binance side를 Side enum으로 변환"""
        return Side.BUY if side_str == "BUY" else Side.SELL

    @staticmethod
    def _parse_order_type(type_str: str) -> OrderType:
        """Binance order type을 OrderType enum으로 변환"""
        type_map = {
            "LIMIT": OrderType.LIMIT,
            "MARKET": OrderType.MARKET,
            "STOP_LOSS": OrderType.STOP_MARKET,
            "STOP_LOSS_LIMIT": OrderType.STOP_LIMIT,
        }
        return type_map.get(type_str, OrderType.LIMIT)

    @staticmethod
    def _parse_order_status(status_str: str) -> OrderStatus:
        """Binance order status를 OrderStatus enum으로 변환"""
        status_map = {
            "NEW": OrderStatus.PENDING,
            "PARTIALLY_FILLED": OrderStatus.PARTIAL,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELED,
            "REJECTED": OrderStatus.CANCELED,
            "EXPIRED": OrderStatus.CANCELED,
        }
        return status_map.get(status_str, OrderStatus.PENDING)

    @staticmethod
    def _parse_time_in_force(tif_str: Optional[str]) -> Optional[TimeInForce]:
        """Binance timeInForce를 TimeInForce enum으로 변환"""
        if not tif_str:
            return None
        tif_map = {
            "GTC": TimeInForce.GTC,
            "IOC": TimeInForce.IOC,
            "FOK": TimeInForce.FOK,
        }
        return tif_map.get(tif_str)

    @staticmethod
    def parse_order_response(binance_response: Dict[str, Any]) -> OpenSpotOrderResponse:
        """주문 생성 성공 응답 파싱"""
        stock_address = ResponseParser._parse_symbol_to_stock_address(binance_response["symbol"])

        order = SpotOrder(
            order_id=str(binance_response["orderId"]),
            stock_address=stock_address,
            side=ResponseParser._parse_side(binance_response["side"]),
            order_type=ResponseParser._parse_order_type(binance_response["type"]),
            price=float(binance_response["price"]) if binance_response.get("price") else None,
            amount=float(binance_response["origQty"]),
            timestamp=binance_response.get("transactTime", int(time.time() * 1000)),
            filled_amount=float(binance_response.get("executedQty", "0")),
            status=ResponseParser._parse_order_status(binance_response["status"]),
            time_in_force=ResponseParser._parse_time_in_force(binance_response.get("timeInForce")),
        )

        return OpenSpotOrderResponse(
            is_success=True,
            order=order,
            error_message=None,
        )

    @staticmethod
    def parse_order_error(exception: Exception) -> OpenSpotOrderResponse:
        """주문 생성 실패 응답 파싱"""
        error_msg = str(exception)

        response = OpenSpotOrderResponse(
            is_success=False,
            order=None,
            error_message=error_msg,
        )

        # 에러 타입별 플래그 설정
        if "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
            response.is_insufficient_balance = True
        elif "min notional" in error_msg.lower():
            response.is_min_notional_error = True
        elif "max notional" in error_msg.lower():
            response.is_max_notional_error = True
        elif "post-only" in error_msg.lower() or "post only" in error_msg.lower():
            response.is_post_only_rejected = True

        return response

    @staticmethod
    def parse_order_status_response(binance_response: Dict[str, Any]) -> OrderCurrentStateResponse:
        """주문 상태 조회 응답 파싱"""
        stock_address = ResponseParser._parse_symbol_to_stock_address(binance_response["symbol"])

        order = SpotOrder(
            order_id=str(binance_response["orderId"]),
            stock_address=stock_address,
            side=ResponseParser._parse_side(binance_response["side"]),
            order_type=ResponseParser._parse_order_type(binance_response["type"]),
            price=float(binance_response["price"]) if binance_response.get("price") else None,
            amount=float(binance_response["origQty"]),
            timestamp=binance_response.get("time", int(time.time() * 1000)),
            filled_amount=float(binance_response.get("executedQty", "0")),
            status=ResponseParser._parse_order_status(binance_response["status"]),
            time_in_force=ResponseParser._parse_time_in_force(binance_response.get("timeInForce")),
        )

        return OrderCurrentStateResponse(
            is_success=True,
            current_order=order,
            error_message=None,
        )

    @staticmethod
    def parse_balance_response(binance_response: Dict[str, Any]) -> CurrentBalanceResponse:
        """계정 잔고 조회 응답 파싱"""
        balances = {}

        for balance_data in binance_response.get("balances", []):
            symbol = balance_data["asset"]
            free = float(balance_data["free"])
            locked = float(balance_data["locked"])
            total = free + locked

            # Token 객체 생성 (total amount)
            if total > 0:  # 잔고가 있는 것만
                token = Token(symbol=symbol, amount=total)
                balances[symbol] = token

        return CurrentBalanceResponse(
            is_success=True,
            result=balances,
            error_message=None,
        )

    @staticmethod
    def parse_ticker_response(binance_response: Dict[str, Any]) -> TickerResponse:
        """Ticker 응답 파싱"""
        # Binance ticker 응답을 TickerResponse 형식으로 변환
        symbol = binance_response["symbol"]
        ticker_data = {
            "timestamp": binance_response.get("closeTime", int(time.time() * 1000)),
            "open": float(binance_response.get("openPrice", 0)),
            "high": float(binance_response.get("highPrice", 0)),
            "low": float(binance_response.get("lowPrice", 0)),
            "current": float(binance_response.get("lastPrice", 0)),
            "volume": float(binance_response.get("volume", 0)),
        }

        return TickerResponse(
            is_success=True,
            result={symbol: ticker_data},
            error_message=None,
        )

    @staticmethod
    def parse_orderbook_response(binance_response: Dict[str, Any]) -> OrderbookResponse:
        """Orderbook 응답 파싱"""
        # bids/asks를 문자열 리스트에서 float tuple로 변환
        bids = [(float(price), float(qty)) for price, qty in binance_response.get("bids", [])]
        asks = [(float(price), float(qty)) for price, qty in binance_response.get("asks", [])]

        return OrderbookResponse(
            is_success=True,
            symbol="",  # symbol은 요청 시 알고 있으므로 여기서는 비워둠
            bids=bids,
            asks=asks,
            timestamp=int(time.time() * 1000),
            error_message=None,
        )
