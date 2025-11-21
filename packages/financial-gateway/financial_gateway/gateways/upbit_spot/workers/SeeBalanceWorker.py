import time
from typing import Dict, Union
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.token import Token
from financial_gateway.structures.see_balance import SeeBalanceRequest, SeeBalanceResponse


class SeeBalanceWorker:
    """현금 자산(reference currency) 조회 Worker

    Upbit API:
    - GET /v1/accounts
    - Weight: Exchange Non-Order (초당 30회, 분당 900회)

    Upbit 특징:
    - currency == unit_currency인 것들이 balance (예: KRW)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeBalanceRequest) -> SeeBalanceResponse:
        send_when = self._utc_now_ms()

        try:
            api_response = await self.throttler.get_accounts()

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeBalanceWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeBalanceRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeBalanceResponse:
        balances_dict: Dict[str, Dict[str, Union[Token, float]]] = {}

        # currencies 필터링
        currencies_filter = request.currencies
        if currencies_filter is not None and len(currencies_filter) == 0:
            currencies_filter = None

        for account_data in api_response:
            currency = account_data.get("currency")
            unit_currency = account_data.get("unit_currency", "KRW")

            # currency == unit_currency인 것만 balance로 분류
            if currency != unit_currency:
                continue

            balance = float(account_data.get("balance", 0))
            locked = float(account_data.get("locked", 0))
            total = balance + locked

            # currencies 필터 적용
            if currencies_filter is not None:
                if currency not in currencies_filter:
                    continue
            else:
                # currencies=None일 때: 거의 0인 잔고 제외
                if total < 0.00000001:
                    continue

            # Token 생성
            balance_token = Token(currency, total)

            balances_dict[currency] = {
                "balance": balance_token,
                "available": balance,
                "promised": locked,
            }

        processed_when = (send_when + receive_when) // 2
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

        if "api-key" in error_str or "signature" in error_str:
            error_code = "AUTHENTICATION_FAILED"
        elif "permission" in error_str:
            error_code = "PERMISSION_DENIED"
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
