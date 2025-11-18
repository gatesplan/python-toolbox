import os
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv
from throttled_api.providers.binance import BinanceSpotThrottler
from binance.spot import Spot
from simple_logger import init_logging, func_logging, logger


class APICallExecutor:
    """
    Binance Spot API 호출 실행자
    BinanceSpotThrottler를 래핑하여 rate limit 관리와 함께 API 호출
    """

    @init_logging(level="INFO")
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("BINANCE_SPOT_API_KEY")
        api_secret = os.getenv("BINANCE_SPOT_API_SECRET")

        if not api_key:
            raise EnvironmentError(
                "BINANCE_SPOT_API_KEY not found in environment variables. "
                "Please set it in .env file or environment."
            )

        if not api_secret:
            raise EnvironmentError(
                "BINANCE_SPOT_API_SECRET not found in environment variables. "
                "Please set it in .env file or environment."
            )

        logger.debug(f"API 키 로드 완료 (key_prefix={api_key[:8]}...)")

        # Binance Spot client 생성
        client = Spot(api_key=api_key, api_secret=api_secret)

        # BinanceSpotThrottler로 래핑
        self.throttler = BinanceSpotThrottler(client=client)
        logger.debug("BinanceSpotThrottler 초기화 완료")

    @func_logging(level="INFO", log_params=True)
    async def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        주문 생성
        POST /api/v3/order
        """
        return await self.throttler.create_order(symbol=symbol, side=side, type=type, **kwargs)

    @func_logging(level="INFO", log_params=True)
    async def cancel_order(self, symbol: str, order_id: int, **kwargs) -> Dict[str, Any]:
        """
        주문 취소
        DELETE /api/v3/order
        """
        return await self.throttler.cancel_order(symbol=symbol, order_id=order_id, **kwargs)

    @func_logging(level="INFO", log_params=True)
    async def get_order(self, symbol: str, order_id: int, **kwargs) -> Dict[str, Any]:
        """
        주문 조회
        GET /api/v3/order
        """
        return await self.throttler.get_order(symbol=symbol, order_id=order_id, **kwargs)

    @func_logging(level="INFO")
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        미체결 주문 목록 조회
        GET /api/v3/openOrders
        """
        return await self.throttler.get_open_orders(symbol=symbol)

    @func_logging(level="INFO")
    async def get_all_orders(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        전체 주문 내역 조회
        GET /api/v3/allOrders
        """
        return await self.throttler.get_all_orders(
            symbol=symbol,
            order_id=order_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    @func_logging(level="INFO")
    async def get_account(self) -> Dict[str, Any]:
        """
        계정 정보 조회
        GET /api/v3/account
        """
        return await self.throttler.get_account()

    @func_logging(level="INFO")
    async def get_my_trades(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        체결 내역 조회
        GET /api/v3/myTrades
        """
        return await self.throttler.get_my_trades(
            symbol=symbol,
            order_id=order_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    @func_logging(level="INFO", log_params=True)
    async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        호가 정보 조회
        GET /api/v3/depth
        """
        return await self.throttler.get_order_book(symbol=symbol, limit=limit)

    @func_logging
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        최근 거래 내역 조회
        GET /api/v3/trades
        """
        return await self.throttler.get_recent_trades(symbol=symbol, limit=limit)

    @func_logging
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[List[Any]]:
        """
        캔들 데이터 조회
        GET /api/v3/klines
        """
        return await self.throttler.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    @func_logging(level="INFO", log_params=True)
    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> Any:
        """
        24시간 가격 변동 통계
        GET /api/v3/ticker/24hr
        """
        return await self.throttler.get_ticker_24hr(symbol=symbol)

    @func_logging
    async def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        """
        최신 가격 조회
        GET /api/v3/ticker/price
        """
        return await self.throttler.get_ticker_price(symbol=symbol)

    @func_logging
    async def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        거래소 정보 조회
        GET /api/v3/exchangeInfo
        """
        return await self.throttler.get_exchange_info(symbol=symbol)

    @func_logging
    async def get_server_time(self) -> Dict[str, Any]:
        """
        서버 시간 조회
        GET /api/v3/time
        """
        return await self.throttler.get_server_time()
