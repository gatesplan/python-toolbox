import time
from typing import Dict, Union, List, Optional
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.symbol import Symbol
from financial_gateway.structures.see_holdings import SeeHoldingsRequest, SeeHoldingsResponse


class SeeHoldingsWorker:
    """보유 자산(거래 대상 자산) 조회 Worker

    Binance API:
    - GET /api/v3/account (Weight: 20)
    - GET /api/v3/myTrades (Weight: 20 per symbol)

    평단가 계산:
    - Binance는 평단가를 직접 제공하지 않음
    - myTrades API로 거래 내역 조회하여 가중평균 매수가 계산
    """

    # Binance 기본 quote currency
    DEFAULT_QUOTE = "USDT"

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeHoldingsRequest) -> SeeHoldingsResponse:
        send_when = self._utc_now_ms()

        try:
            # Account 정보 조회
            await self.throttler._check_and_wait(20)
            api_response = await self.throttler.get_account()

            receive_when = self._utc_now_ms()
            return await self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeHoldingsWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    async def _decode_success(
        self, request: SeeHoldingsRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeHoldingsResponse:
        # Binance account response:
        # {
        #   "balances": [
        #     {"asset": "BTC", "free": "0.5", "locked": "0.2"},
        #     {"asset": "ETH", "free": "10.0", "locked": "3.0"},
        #     ...
        #   ],
        #   "updateTime": 1234567890000
        # }

        balances_data = api_response.get("balances", [])
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

        # 각 balance 처리
        for balance_data in balances_data:
            asset = balance_data.get("asset")
            free = float(balance_data.get("free", 0))
            locked = float(balance_data.get("locked", 0))
            total = free + locked

            # symbols 필터 적용
            if symbols_filter is not None:
                # 지정된 symbols의 base asset만 포함
                if asset not in asset_to_quote:
                    continue
                # 0 잔고여도 포함
                quote = asset_to_quote[asset]
            else:
                # symbols=None: 0.001 미만 잔고 제외 (dust filtering)
                if total < 0.001:
                    continue
                quote = self.DEFAULT_QUOTE

            # 평단가 계산
            avg_buy_price = await self._calculate_avg_buy_price(asset, quote)

            # Pair 생성
            asset_token = Token(asset, total)
            value_token = Token(quote, total * avg_buy_price)
            balance_pair = Pair(asset=asset_token, value=value_token)

            holdings_dict[asset] = {
                "balance": balance_pair,
                "available": free,
                "promised": locked,
            }

        # processed_when: API 응답의 updateTime 우선, 없으면 추정
        processed_when = api_response.get("updateTime") or (send_when + receive_when) // 2
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

    async def _calculate_avg_buy_price(self, base: str, quote: str) -> float:
        """거래 내역으로부터 가중평균 매수가 계산

        Args:
            base: 기초 자산 (예: BTC)
            quote: 견적 자산 (예: USDT)

        Returns:
            평단가 (weighted average buy price)
            거래 내역이 없으면 0 반환
        """
        try:
            symbol = f"{base}{quote}"

            # myTrades 조회 (최근 500개까지)
            await self.throttler._check_and_wait(20)
            trades = await self.throttler.get_my_trades(symbol=symbol, limit=500)

            if not trades:
                logger.warning(f"{symbol} 거래 내역 없음, 평단가 0으로 설정")
                return 0.0

            # BUY 거래만 필터링하여 가중평균 계산
            total_qty = 0.0
            total_cost = 0.0

            for trade in trades:
                # Binance myTrades response:
                # {
                #   "price": "50000.00",
                #   "qty": "0.1",
                #   "commission": "0.00005",
                #   "commissionAsset": "BTC",
                #   "isBuyer": true,
                #   ...
                # }

                is_buyer = trade.get("isBuyer", False)
                if not is_buyer:
                    # SELL 거래는 평단가 계산에서 제외
                    continue

                price = float(trade.get("price", 0))
                qty = float(trade.get("qty", 0))

                total_qty += qty
                total_cost += price * qty

            if total_qty == 0:
                logger.warning(f"{symbol} BUY 거래 없음, 평단가 0으로 설정")
                return 0.0

            avg_price = total_cost / total_qty
            logger.debug(f"{symbol} 평단가 계산 완료: {avg_price:.8f} (거래 수: {len(trades)})")
            return avg_price

        except Exception as e:
            logger.error(f"{base}/{quote} 평단가 계산 실패: {e}, 0으로 설정")
            return 0.0

    def _decode_error(
        self, request: SeeHoldingsRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeHoldingsResponse:
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
        elif "invalid" in error_str and "symbol" in error_str:
            error_code = "INVALID_SYMBOL"
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
