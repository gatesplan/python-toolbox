import time
from typing import Dict, Union
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.token import Token
from financial_gateway.structures.see_balance import SeeBalanceRequest, SeeBalanceResponse


class SeeBalanceWorker:
    """현금 자산(reference currency) 조회 Worker

    Binance API:
    - GET /api/v3/account
    - Weight: 20
    """

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeBalanceRequest) -> SeeBalanceResponse:
        send_when = self._utc_now_ms()

        try:
            # Account 정보 조회
            await self.throttler._check_and_wait(20)
            api_response = await self.throttler.get_account()

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeBalanceWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeBalanceRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeBalanceResponse:
        # Binance account response:
        # {
        #   "balances": [
        #     {"asset": "USDT", "free": "800.0", "locked": "200.0"},
        #     {"asset": "BTC", "free": "0.5", "locked": "0.2"},
        #     ...
        #   ],
        #   "updateTime": 1234567890000
        # }

        balances_data = api_response.get("balances", [])
        balances_dict: Dict[str, Dict[str, Union[Token, float]]] = {}

        # currencies 필터링
        currencies_filter = request.currencies
        if currencies_filter is not None and len(currencies_filter) == 0:
            currencies_filter = None

        for balance_data in balances_data:
            asset = balance_data.get("asset")
            free = float(balance_data.get("free", 0))
            locked = float(balance_data.get("locked", 0))
            total = free + locked

            # currencies 필터 적용
            if currencies_filter is not None:
                if asset not in currencies_filter:
                    continue
            else:
                # currencies=None일 때: 거의 0인 잔고 제외
                if total < 0.00000001:
                    continue

            # Token 생성
            balance_token = Token(asset, total)

            balances_dict[asset] = {
                "balance": balance_token,
                "available": free,
                "promised": locked,
            }

        # processed_when: API 응답의 updateTime 우선, 없으면 추정
        processed_when = api_response.get("updateTime") or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeBalanceResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            balances=balances_dict,
        )

    def _decode_error(
        self, request: SeeBalanceRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeBalanceResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error).lower()

        # 에러 코드 매핑
        if "api-key" in error_str or "signature" in error_str:
            error_code = "AUTHENTICATION_FAILED"
        elif "permission" in error_str or "authorized" in error_str:
            error_code = "PERMISSION_DENIED"
        elif "rate" in error_str or "limit" in error_str:
            error_code = "RATE_LIMIT_EXCEEDED"
        elif "network" in error_str or "connection" in error_str:
            error_code = "NETWORK_ERROR"
        else:
            error_code = "API_ERROR"

        return SeeBalanceResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
