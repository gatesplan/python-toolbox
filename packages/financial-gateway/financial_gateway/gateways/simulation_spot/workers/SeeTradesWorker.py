# SeeTradesWorker - Simulation Spot Gateway

from typing import List
from simple_logger import init_logging, func_logging
from financial_assets.stock_address import StockAddress
from financial_assets.trade import SpotTrade
from financial_gateway.structures.see_trades.request import SeeTradesRequest
from financial_gateway.structures.see_trades.response import SeeTradesResponse


class SeeTradesWorker:
    # 체결 내역 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeTradesRequest) -> SeeTradesResponse:
        # 체결 내역 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. Exchange에서 trade history 조회
            if request.order is not None:
                # 특정 order의 trades만 조회
                order_id = request.order.order_id
                all_trades = self.exchange.get_trade_history(symbol)
                trades = [t for t in all_trades if t.order.order_id == order_id]
            else:
                # 마켓 전체 trades 조회
                trades = self.exchange.get_trade_history(symbol)

            receive_when = self._get_timestamp_ms()

            # 3. 최신순 정렬 (timestamp 내림차순)
            trades = sorted(trades, key=lambda t: t.timestamp, reverse=True)

            # 4. limit 적용
            if request.limit is not None and request.limit > 0:
                trades = trades[:request.limit]

            # 5. Decode: → Response
            return self._decode_success(request, trades, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "INVALID_SYMBOL", str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_symbol(self, address: StockAddress) -> str:
        # StockAddress → symbol (BTC/USDT)
        return address.to_symbol().to_slash()

    def _decode_success(
        self,
        request: SeeTradesRequest,
        trades: List[SpotTrade],
        send_when: int,
        receive_when: int
    ) -> SeeTradesResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTradesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            trades=trades
        )

    def _decode_error(
        self,
        request: SeeTradesRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeTradesResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTradesResponse(
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
