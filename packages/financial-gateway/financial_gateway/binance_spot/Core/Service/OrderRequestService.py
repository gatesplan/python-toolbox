"""
주문 요청 서비스
Core 계층(APICallExecutor, RequestConverter, ResponseParser)을 조합하여 주문 관련 비즈니스 로직 제공
"""
from typing import Dict, Any
from simple_logger import init_logging, func_logging, logger
from financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor import APICallExecutor
from financial_gateway.binance_spot.Core.RequestConverter.RequestConverter import RequestConverter
from financial_gateway.binance_spot.Core.ResponseParser.ResponseParser import ResponseParser
from financial_gateway.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
    CloseOrderRequest,
    OrderCurrentStateRequest,
)
from financial_gateway.response import (
    OpenSpotOrderResponse,
    CloseLimitOrderResponse,
    OrderCurrentStateResponse,
)


class OrderRequestService:
    """
    주문 요청 서비스
    Core 계층을 조합하여 주문 생성/취소/조회 기능 제공
    """

    @init_logging(level="INFO")
    def __init__(self):
        """서비스 초기화"""
        self.executor = APICallExecutor()

    @func_logging(level="INFO")
    async def limit_buy(self, request: LimitBuyOrderRequest) -> OpenSpotOrderResponse:
        """
        지정가 매수 주문

        Args:
            request: 지정가 매수 주문 요청

        Returns:
            OpenSpotOrderResponse: 주문 생성 결과
        """
        try:
            # 1. Request -> API 파라미터 변환
            params = RequestConverter.convert_limit_buy_order(request)
            logger.debug(f"주문 파라미터 변환 완료: {params}")

            # 2. API 호출
            binance_response = await self.executor.create_order(**params)
            logger.debug("API 호출 성공")

            # 3. 응답 파싱
            return ResponseParser.parse_order_response(binance_response)

        except Exception as e:
            # 4. 에러 처리
            logger.debug(f"주문 실패: {str(e)}")
            return ResponseParser.parse_order_error(e)

    @func_logging(level="INFO")
    async def limit_sell(self, request: LimitSellOrderRequest) -> OpenSpotOrderResponse:
        """
        지정가 매도 주문

        Args:
            request: 지정가 매도 주문 요청

        Returns:
            OpenSpotOrderResponse: 주문 생성 결과
        """
        try:
            params = RequestConverter.convert_limit_sell_order(request)
            logger.debug(f"주문 파라미터 변환 완료: {params}")
            binance_response = await self.executor.create_order(**params)
            logger.debug("API 호출 성공")
            return ResponseParser.parse_order_response(binance_response)

        except Exception as e:
            logger.debug(f"주문 실패: {str(e)}")
            return ResponseParser.parse_order_error(e)

    @func_logging(level="INFO")
    async def market_buy(self, request: MarketBuyOrderRequest) -> OpenSpotOrderResponse:
        """
        시장가 매수 주문

        Args:
            request: 시장가 매수 주문 요청

        Returns:
            OpenSpotOrderResponse: 주문 생성 결과
        """
        try:
            params = RequestConverter.convert_market_buy_order(request)
            logger.debug(f"주문 파라미터 변환 완료: {params}")
            binance_response = await self.executor.create_order(**params)
            logger.debug("API 호출 성공")
            return ResponseParser.parse_order_response(binance_response)

        except Exception as e:
            logger.debug(f"주문 실패: {str(e)}")
            return ResponseParser.parse_order_error(e)

    @func_logging(level="INFO")
    async def market_sell(self, request: MarketSellOrderRequest) -> OpenSpotOrderResponse:
        """
        시장가 매도 주문

        Args:
            request: 시장가 매도 주문 요청

        Returns:
            OpenSpotOrderResponse: 주문 생성 결과
        """
        try:
            params = RequestConverter.convert_market_sell_order(request)
            logger.debug(f"주문 파라미터 변환 완료: {params}")
            binance_response = await self.executor.create_order(**params)
            logger.debug("API 호출 성공")
            return ResponseParser.parse_order_response(binance_response)

        except Exception as e:
            logger.debug(f"주문 실패: {str(e)}")
            return ResponseParser.parse_order_error(e)

    @func_logging(level="INFO")
    async def cancel_order(self, request: CloseOrderRequest) -> CloseLimitOrderResponse:
        """
        주문 취소

        Args:
            request: 주문 취소 요청

        Returns:
            CancelOrderResponse: 취소 결과
        """
        try:
            params = RequestConverter.convert_cancel_order(request)
            logger.debug(f"취소 파라미터: {params}")
            binance_response = await self.executor.cancel_order(**params)
            logger.debug("주문 취소 성공")

            # 취소 성공 응답
            return CloseLimitOrderResponse(
                is_success=True,
                error_message=None,
            )

        except Exception as e:
            logger.debug(f"주문 취소 실패: {str(e)}")
            return CloseLimitOrderResponse(
                is_success=False,
                error_message=str(e),
            )

    @func_logging(level="INFO")
    async def get_order_status(self, request: OrderCurrentStateRequest) -> OrderCurrentStateResponse:
        """
        주문 상태 조회

        Args:
            request: 주문 상태 조회 요청

        Returns:
            OrderCurrentStateResponse: 주문 상태 정보
        """
        try:
            params = RequestConverter.convert_order_status_request(request)
            binance_response = await self.executor.get_order(**params)
            return ResponseParser.parse_order_status_response(binance_response)

        except Exception as e:
            logger.debug(f"주문 조회 실패: {str(e)}")
            return OrderCurrentStateResponse(
                is_success=False,
                current_order=None,
                error_message=str(e),
            )
