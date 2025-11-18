"""
시장 데이터 서비스
Core 계층(APICallExecutor, RequestConverter, ResponseParser)을 조합하여 시장 데이터 조회 기능 제공
"""
from simple_logger import init_logging, func_logging, logger
from financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor import APICallExecutor
from financial_gateway.binance_spot.Core.RequestConverter.RequestConverter import RequestConverter
from financial_gateway.binance_spot.Core.ResponseParser.ResponseParser import ResponseParser
from financial_gateway.request import (
    TickerRequest,
    OrderbookRequest,
    CurrentBalanceRequest,
)
from financial_gateway.response import (
    TickerResponse,
    OrderbookResponse,
    CurrentBalanceResponse,
)


class MarketDataService:
    """
    시장 데이터 서비스
    Core 계층을 조합하여 Ticker, Orderbook, Balance 조회 기능 제공
    """

    @init_logging(level="INFO")
    def __init__(self):
        """서비스 초기화"""
        self.executor = APICallExecutor()

    @func_logging(level="INFO")
    async def get_ticker(self, request: TickerRequest) -> TickerResponse:
        """
        Ticker 정보 조회

        Args:
            request: Ticker 조회 요청

        Returns:
            TickerResponse: Ticker 정보
        """
        try:
            symbol = f"{request.address.base}{request.address.quote}"
            logger.debug(f"Ticker 조회: {symbol}")
            binance_response = await self.executor.get_ticker_24hr(symbol=symbol)
            return ResponseParser.parse_ticker_response(binance_response)

        except Exception as e:
            logger.debug(f"Ticker 조회 실패: {str(e)}")
            return TickerResponse(
                is_success=False,
                result={},
                error_message=str(e),
            )

    @func_logging(level="INFO")
    async def get_orderbook(self, request: OrderbookRequest) -> OrderbookResponse:
        """
        호가 정보 조회

        Args:
            request: Orderbook 조회 요청

        Returns:
            OrderbookResponse: 호가 정보
        """
        try:
            symbol = f"{request.address.base}{request.address.quote}"
            limit = request.limit if hasattr(request, 'limit') and request.limit else 10
            logger.debug(f"Orderbook 조회: {symbol} (limit={limit})")
            binance_response = await self.executor.get_depth(symbol=symbol, limit=limit)

            response = ResponseParser.parse_orderbook_response(binance_response)
            response.symbol = symbol
            return response

        except Exception as e:
            logger.debug(f"Orderbook 조회 실패: {str(e)}")
            return OrderbookResponse(
                is_success=False,
                symbol="",
                bids=[],
                asks=[],
                timestamp=0,
                error_message=str(e),
            )

    @func_logging(level="INFO")
    async def get_balance(self, request: CurrentBalanceRequest) -> CurrentBalanceResponse:
        """
        계정 잔고 조회

        Args:
            request: 잔고 조회 요청

        Returns:
            CurrentBalanceResponse: 잔고 정보
        """
        try:
            binance_response = await self.executor.get_account()
            balance_count = len(binance_response.get("balances", []))
            logger.debug(f"계정 정보 조회 완료 (총 {balance_count}개 자산)")
            return ResponseParser.parse_balance_response(binance_response)

        except Exception as e:
            logger.debug(f"계정 정보 조회 실패: {str(e)}")
            return CurrentBalanceResponse(
                is_success=False,
                result={},
                error_message=str(e),
            )
