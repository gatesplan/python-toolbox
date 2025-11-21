import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.trade import SpotTrade
from financial_assets.order import SpotOrder
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.constants import OrderSide, OrderType
from financial_gateway.structures.see_trades import SeeTradesRequest, SeeTradesResponse


class SeeTradesWorker:
    """체결 내역 조회 Worker

    Upbit API:
    - GET /v1/trades/ticks (공개 - 마켓 전체 체결)
    - GET /v1/order (인증 - 특정 주문 체결, trades 배열 포함)
    - Weight: Quotation (초당 10회, 분당 600회) / Exchange Non-Order (초당 30회, 분당 900회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeTradesRequest) -> SeeTradesResponse:
        send_when = self._utc_now_ms()

        try:
            if request.order is not None:
                # 특정 주문의 체결 내역 조회
                trades = await self._get_order_trades(request, send_when)
            else:
                # 마켓 전체 체결 내역 조회 (공개 API)
                trades = await self._get_market_trades(request, send_when)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, trades, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeTradesWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    async def _get_order_trades(self, request: SeeTradesRequest, send_when: int) -> List[SpotTrade]:
        """특정 주문의 체결 내역 조회 (GET /v1/order의 trades 배열)"""
        order = request.order

        # 주문 조회 (trades 배열 포함)
        api_response = await self.throttler.get_order(
            uuid=order.order_id if not order.client_order_id else None,
            identifier=order.client_order_id,
        )

        # trades 배열 파싱
        trades_data = api_response.get("trades", [])
        trades = []

        for trade_data in trades_data:
            # Upbit order trades 구조:
            # {
            #   "market": "KRW-BTC",
            #   "uuid": "trade-uuid",
            #   "price": "50000000",
            #   "volume": "0.1",
            #   "funds": "5000000",
            #   "side": "bid",
            #   "created_at": "2021-03-21T15:24:11+09:00"
            # }

            trade_id = trade_data.get("uuid")
            price = float(trade_data.get("price", 0))
            volume = float(trade_data.get("volume", 0))
            funds = float(trade_data.get("funds", 0))
            side_str = trade_data.get("side", "bid")
            timestamp = self._parse_timestamp(trade_data.get("created_at")) or send_when

            # side 매핑
            side = OrderSide.BUY if side_str == "bid" else OrderSide.SELL

            # SpotTrade 생성
            spot_trade = SpotTrade(
                trade_id=trade_id,
                order=SpotOrder(
                    order_id=order.order_id,
                    stock_address=request.address,
                    side=side,
                    order_type=order.order_type,
                    price=price,
                    amount=volume,
                    timestamp=timestamp,
                    client_order_id=order.client_order_id,
                ),
                pair=Pair(
                    asset=Token(request.address.base, volume),
                    value=Token(request.address.quote, funds)
                ),
                timestamp=timestamp,
                fee=None  # Upbit trades에 수수료 정보 없음
            )
            trades.append(spot_trade)

        # timestamp 내림차순 정렬 (최신순)
        trades.sort(key=lambda t: t.timestamp, reverse=True)

        return trades

    async def _get_market_trades(self, request: SeeTradesRequest, send_when: int) -> List[SpotTrade]:
        """마켓 전체 체결 내역 조회 (GET /v1/trades/ticks)"""
        market = f"{request.address.quote}-{request.address.base}"
        count = request.limit if request.limit else 100

        api_response = await self.throttler.get_trades_ticks(market=market, count=count)

        # Upbit trades 응답:
        # [
        #   {
        #     "market": "KRW-BTC",
        #     "trade_date_utc": "2021-03-21",
        #     "trade_time_utc": "06:24:11",
        #     "timestamp": 1616305451000,
        #     "trade_price": 50000000,
        #     "trade_volume": 0.1,
        #     "prev_closing_price": 49500000,
        #     "change_price": 500000,
        #     "ask_bid": "ASK",  # ASK(매도), BID(매수)
        #     "sequential_id": 123456789
        #   },
        #   ...
        # ]

        trades = []
        for trade_data in api_response:
            trade_id = str(trade_data.get("sequential_id"))
            price = float(trade_data.get("trade_price", 0))
            volume = float(trade_data.get("trade_volume", 0))
            timestamp = trade_data.get("timestamp", send_when)

            # ask_bid → side 매핑
            ask_bid = trade_data.get("ask_bid", "ASK")
            side = OrderSide.SELL if ask_bid == "ASK" else OrderSide.BUY

            # SpotTrade 생성 (공개 데이터이므로 Order 정보 최소화)
            spot_trade = SpotTrade(
                trade_id=trade_id,
                order=SpotOrder(
                    order_id="unknown",  # 공개 API는 order_id 제공 안함
                    stock_address=request.address,
                    side=side,
                    order_type=OrderType.MARKET,  # 추정
                    price=price,
                    amount=volume,
                    timestamp=timestamp,
                ),
                pair=Pair(
                    asset=Token(request.address.base, volume),
                    value=Token(request.address.quote, price * volume)
                ),
                timestamp=timestamp,
                fee=None
            )
            trades.append(spot_trade)

        # timestamp 내림차순 정렬 (최신순)
        trades.sort(key=lambda t: t.timestamp, reverse=True)

        return trades

    def _decode_success(
        self, request: SeeTradesRequest, trades: List[SpotTrade], send_when: int, receive_when: int
    ) -> SeeTradesResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTradesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            trades=trades,
        )

    def _decode_error(
        self, request: SeeTradesRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeTradesResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTradesResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code="API_ERROR",
            error_message=str(error),
        )

    def _parse_timestamp(self, timestamp_str: str) -> int:
        if not timestamp_str:
            return None
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except:
            return None

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
