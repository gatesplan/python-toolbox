# SeeHoldingsWorker - Simulation Spot Gateway

from typing import Dict, Union
from simple_logger import init_logging, func_logging
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.symbol import Symbol
from financial_gateway.structures.see_holdings.request import SeeHoldingsRequest
from financial_gateway.structures.see_holdings.response import SeeHoldingsResponse


class SeeHoldingsWorker:
    # 보유 자산 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeHoldingsRequest) -> SeeHoldingsResponse:
        # 보유 자산 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 조회할 positions 결정
            all_positions = self.exchange.get_positions()

            if request.symbols is None or len(request.symbols) == 0:
                # 전체 조회 - 0.001 미만 제외
                tickers = [ticker for ticker, amount in all_positions.items() if amount >= 0.001]
            else:
                # 특정 symbols 조회
                tickers = [symbol.to_dash() for symbol in request.symbols]

            # 2. 각 ticker별 holdings 조회
            holdings = {}
            for ticker in tickers:
                # ticker → Symbol (BTC-USDT → Symbol("BTC-USDT"))
                symbol = Symbol(ticker)
                base = symbol.base
                quote = symbol.quote

                # 총 보유량
                total_amount = all_positions.get(ticker, 0.0)

                # available/locked
                available = self.exchange._portfolio.get_available_position(ticker)
                locked = self.exchange._portfolio.get_locked_position(ticker)

                # book_value (평단가 * 수량)
                book_value = self.exchange._position_manager.get_position_book_value(ticker)

                # Pair 생성
                balance_pair = Pair(
                    asset=Token(base, total_amount),
                    value=Token(quote, book_value)
                )

                holdings[base] = {
                    "balance": balance_pair,
                    "available": available,
                    "promised": locked
                }

            receive_when = self._get_timestamp_ms()

            # 3. Decode: → Response
            return self._decode_success(request, holdings, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeHoldingsRequest,
        holdings: Dict[str, Dict[str, Union[Pair, float]]],
        send_when: int,
        receive_when: int
    ) -> SeeHoldingsResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeHoldingsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            holdings=holdings
        )

    def _decode_error(
        self,
        request: SeeHoldingsRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeHoldingsResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeHoldingsResponse(
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
