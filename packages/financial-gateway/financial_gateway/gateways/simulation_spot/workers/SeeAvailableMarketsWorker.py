# SeeAvailableMarketsWorker - Simulation Spot Gateway

from typing import List
from simple_logger import init_logging, func_logging
from financial_assets.market_info import MarketInfo
from financial_gateway.structures.see_available_markets.request import SeeAvailableMarketsRequest
from financial_gateway.structures.see_available_markets.response import SeeAvailableMarketsResponse


class SeeAvailableMarketsWorker:
    # 거래 가능 마켓 목록 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeAvailableMarketsRequest) -> SeeAvailableMarketsResponse:
        # 마켓 목록 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # Exchange에서 마켓 목록 조회
            markets_data = self.exchange.get_available_markets()
            receive_when = self._get_timestamp_ms()

            # dict → MarketInfo 변환
            markets = []
            for market_dict in markets_data:
                market_info = MarketInfo(
                    symbol=market_dict["symbol"],
                    status=market_dict["status"]
                )
                markets.append(market_info)

            # limit 적용
            if request.limit is not None and request.limit > 0:
                markets = markets[:request.limit]

            # Decode: → Response
            return self._decode_success(request, markets, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeAvailableMarketsRequest,
        markets: List[MarketInfo],
        send_when: int,
        receive_when: int
    ) -> SeeAvailableMarketsResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            markets=markets
        )

    def _decode_error(
        self,
        request: SeeAvailableMarketsRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeAvailableMarketsResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000
