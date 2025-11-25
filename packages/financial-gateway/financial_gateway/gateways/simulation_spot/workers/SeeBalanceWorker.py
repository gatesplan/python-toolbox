# SeeBalanceWorker - Simulation Spot Gateway

from typing import Dict, Union
from simple_logger import init_logging, func_logging
from financial_assets.token import Token
from financial_gateway.structures.see_balance.request import SeeBalanceRequest
from financial_gateway.structures.see_balance.response import SeeBalanceResponse


class SeeBalanceWorker:
    # 잔고 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeBalanceRequest) -> SeeBalanceResponse:
        # 잔고 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 조회할 currencies 결정
            if request.currencies is None or len(request.currencies) == 0:
                # 전체 조회
                currencies = self.exchange._portfolio.get_currencies()
            else:
                currencies = request.currencies

            # 2. 각 currency별 잔고 조회
            balances = {}
            for currency in currencies:
                available = self.exchange._portfolio.get_available_balance(currency)
                locked = self.exchange._portfolio.get_locked_balance(currency)
                total = available + locked

                # 0 잔고 제외 (전체 조회일 때만)
                if request.currencies is None and total < 0.0000001:
                    continue

                # balance Token 생성
                balance_token = Token(currency, total)

                balances[currency] = {
                    "balance": balance_token,
                    "available": available,
                    "promised": locked
                }

            receive_when = self._get_timestamp_ms()

            # 3. Decode: → Response
            return self._decode_success(request, balances, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeBalanceRequest,
        balances: Dict[str, Dict[str, Union[Token, float]]],
        send_when: int,
        receive_when: int
    ) -> SeeBalanceResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeBalanceResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            balances=balances
        )

    def _decode_error(
        self,
        request: SeeBalanceRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeBalanceResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeBalanceResponse(
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
