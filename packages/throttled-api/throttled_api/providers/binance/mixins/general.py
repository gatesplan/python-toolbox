"""
General Endpoints Mixin
"""
from typing import Any, Optional, List


class GeneralMixin:
    """
    General endpoints (connectivity, server time, exchange info)

    모든 메서드는 BaseThrottler의 _check_and_wait()를 사용
    """

    async def ping(self) -> dict:
        """
        Test connectivity to the Rest API

        GET /api/v3/ping
        Weight: 1

        Returns:
            {"status": "ok"} or similar
        """
        await self._check_and_wait(1)
        return self.client.ping()

    async def get_server_time(self) -> dict:
        """
        Get server time

        GET /api/v3/time
        Weight: 1

        Returns:
            {"serverTime": 1234567890000}
        """
        await self._check_and_wait(1)
        return self.client.time()

    async def get_exchange_info(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> dict:
        """
        Get exchange trading rules and symbol information

        GET /api/v3/exchangeInfo
        Weight: 20 (no symbols), 2 (with symbol/symbols)

        Args:
            symbol: 단일 symbol (예: "BTCUSDT")
            symbols: 여러 symbol 리스트 (예: ["BTCUSDT", "ETHUSDT"])

        Returns:
            Exchange info with symbols, rate limits, etc.
        """
        # symbol 또는 symbols가 있으면 weight=2, 없으면 weight=20
        weight = 2 if (symbol or symbols) else 20

        await self._check_and_wait(weight)
        return self.client.exchange_info(symbol=symbol, symbols=symbols)
