import time
from typing import Dict, Union
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_gateway.structures.see_holdings import SeeHoldingsRequest, SeeHoldingsResponse


class SeeHoldingsWorker:
    """보유 자산(거래 대상 자산) 조회 Worker

    Upbit API:
    - GET /v1/accounts
    - Weight: Exchange Non-Order (초당 30회, 분당 900회)

    Upbit 특징:
    - avg_buy_price를 직접 제공! (평단가 계산 불필요)
    - currency가 KRW가 아닌 것들이 holdings
    """

    # Upbit 기본 quote currency
    DEFAULT_QUOTE = "KRW"

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeHoldingsRequest) -> SeeHoldingsResponse:
        send_when = self._utc_now_ms()

        try:
            api_response = await self.throttler.get_accounts()

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeHoldingsWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeHoldingsRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeHoldingsResponse:
        # Upbit 응답 구조:
        # [
        #   {
        #     "currency": "BTC",
        #     "balance": "0.5",
        #     "locked": "0.2",
        #     "avg_buy_price": "50000000",  # 평단가 직접 제공!
        #     "avg_buy_price_modified": true,
        #     "unit_currency": "KRW"
        #   }
        # ]

        holdings_dict: Dict[str, Dict[str, Union[Pair, float]]] = {}

        # symbols 파라미터 처리
        symbols_filter = request.symbols
        if symbols_filter is not None and len(symbols_filter) == 0:
            symbols_filter = None

        # symbols로부터 asset → quote 매핑 생성
        asset_to_quote = {}
        if symbols_filter is not None:
            for symbol in symbols_filter:
                base = symbol.base
                quote = symbol.quote
                asset_to_quote[base] = quote

        for account_data in api_response:
            currency = account_data.get("currency")
            unit_currency = account_data.get("unit_currency", "KRW")

            # unit_currency가 같은 것(예: KRW-KRW)은 balance로 분류 → 제외
            if currency == unit_currency:
                continue

            balance = float(account_data.get("balance", 0))
            locked = float(account_data.get("locked", 0))
            total = balance + locked
            avg_buy_price = float(account_data.get("avg_buy_price", 0))

            # symbols 필터 적용
            if symbols_filter is not None:
                # 지정된 symbols의 base asset만 포함
                if currency not in asset_to_quote:
                    continue
                # 0 잔고여도 포함
                quote = asset_to_quote[currency]
            else:
                # symbols=None: 0.001 미만 잔고 제외 (dust filtering)
                if total < 0.001:
                    continue
                quote = unit_currency or self.DEFAULT_QUOTE

            # Pair 생성 (Upbit은 avg_buy_price 직접 제공!)
            asset_token = Token(currency, total)
            value_token = Token(quote, total * avg_buy_price)
            balance_pair = Pair(asset=asset_token, value=value_token)

            holdings_dict[currency] = {
                "balance": balance_pair,
                "available": balance,
                "promised": locked,
            }

        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeHoldingsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            holdings=holdings_dict,
        )

    def _decode_error(
        self, request: SeeHoldingsRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeHoldingsResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error).lower()

        if "api-key" in error_str or "signature" in error_str:
            error_code = "AUTHENTICATION_FAILED"
        elif "permission" in error_str:
            error_code = "PERMISSION_DENIED"
        else:
            error_code = "API_ERROR"

        return SeeHoldingsResponse(
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
