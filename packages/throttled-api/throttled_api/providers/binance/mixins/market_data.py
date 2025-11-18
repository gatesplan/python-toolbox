"""
Market Data Endpoints Mixin
"""
from typing import Any, Optional, List


class MarketDataMixin:
    """
    Market Data endpoints (depth, trades, klines, ticker, etc.)
    """

    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100,
    ) -> dict:
        """
        Get order book (depth)

        GET /api/v3/depth
        Weight: 5 (limit <= 100), 25 (limit <= 500), 50 (limit <= 1000), 250 (limit <= 5000)

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            limit: Depth limit (default 100, max 5000)

        Returns:
            {"lastUpdateId": ..., "bids": [...], "asks": [...]}
        """
        if limit <= 100:
            weight = 5
        elif limit <= 500:
            weight = 25
        elif limit <= 1000:
            weight = 50
        else:
            weight = 250

        await self._check_and_wait(weight)
        return self.client.depth(symbol=symbol, limit=limit)

    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[dict]:
        """
        Get recent trades

        GET /api/v3/trades
        Weight: 25

        Args:
            symbol: Trading pair symbol
            limit: Number of trades (default 500, max 1000)

        Returns:
            List of recent trades
        """
        await self._check_and_wait(25)
        return self.client.trades(symbol=symbol, limit=limit)

    async def get_historical_trades(
        self,
        symbol: str,
        limit: int = 500,
        from_id: Optional[int] = None,
    ) -> List[dict]:
        """
        Get historical trades

        GET /api/v3/historicalTrades
        Weight: 25

        Args:
            symbol: Trading pair symbol
            limit: Number of trades (default 500, max 1000)
            from_id: Trade ID to fetch from

        Returns:
            List of historical trades
        """
        await self._check_and_wait(25)
        return self.client.historical_trades(
            symbol=symbol, limit=limit, fromId=from_id
        )

    async def get_aggregate_trades(
        self,
        symbol: str,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get compressed aggregate trades

        GET /api/v3/aggTrades
        Weight: 2

        Args:
            symbol: Trading pair symbol
            from_id: Trade ID to fetch from
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Number of trades (default 500, max 1000)

        Returns:
            List of aggregate trades
        """
        await self._check_and_wait(2)
        return self.client.agg_trades(
            symbol=symbol,
            fromId=from_id,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[list]:
        """
        Get kline/candlestick data

        GET /api/v3/klines
        Weight: 2

        Args:
            symbol: Trading pair symbol
            interval: Kline interval (e.g., "1m", "1h", "1d")
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Number of klines (default 500, max 1000)

        Returns:
            List of klines (OHLCV)
        """
        await self._check_and_wait(2)
        return self.client.klines(
            symbol=symbol,
            interval=interval,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )

    async def get_ui_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[list]:
        """
        Get UI-optimized kline/candlestick data

        GET /api/v3/uiKlines
        Weight: 2

        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Number of klines (default 500, max 1000)

        Returns:
            List of UI klines
        """
        await self._check_and_wait(2)
        return self.client.ui_klines(
            symbol=symbol,
            interval=interval,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )

    async def get_avg_price(self, symbol: str) -> dict:
        """
        Get average price

        GET /api/v3/avgPrice
        Weight: 2

        Args:
            symbol: Trading pair symbol

        Returns:
            {"mins": 5, "price": "..."}
        """
        await self._check_and_wait(2)
        return self.client.avg_price(symbol=symbol)

    async def get_ticker(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        type: str = "FULL",
    ) -> dict:
        """
        Get 24hr rolling window price change statistics

        GET /api/v3/ticker/24hr
        Weight: 2 (single symbol), 40 (1-20 symbols), 80 (all or 100+)

        Args:
            symbol: 단일 symbol
            symbols: 여러 symbol 리스트
            type: Ticker type ("FULL" or "MINI")

        Returns:
            Ticker data
        """
        # symbol 개수에 따라 weight 계산
        if symbol:
            weight = 2
        elif symbols:
            count = len(symbols)
            if count <= 20:
                weight = 40
            elif count <= 100:
                weight = 40
            else:
                weight = 80
        else:
            # 전체 조회
            weight = 80

        await self._check_and_wait(weight)
        return self.client.ticker_24hr(symbol=symbol, symbols=symbols, type=type)

    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> dict:
        """
        Alias for get_ticker with single symbol

        GET /api/v3/ticker/24hr
        Weight: 2

        Args:
            symbol: Trading pair symbol

        Returns:
            24hr ticker data
        """
        return await self.get_ticker(symbol=symbol)

    async def get_ticker_price(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> dict:
        """
        Get symbol price ticker

        GET /api/v3/ticker/price
        Weight: 2 (single symbol), 4 (all symbols)

        Args:
            symbol: 단일 symbol
            symbols: 여러 symbol 리스트

        Returns:
            Price ticker
        """
        weight = 2 if symbol else 4

        await self._check_and_wait(weight)
        return self.client.ticker_price(symbol=symbol, symbols=symbols)

    async def get_orderbook_ticker(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> dict:
        """
        Get best bid/ask price

        GET /api/v3/ticker/bookTicker
        Weight: 2 (single symbol), 4 (all symbols)

        Args:
            symbol: 단일 symbol
            symbols: 여러 symbol 리스트

        Returns:
            Book ticker (best bid/ask)
        """
        weight = 2 if symbol else 4

        await self._check_and_wait(weight)
        return self.client.book_ticker(symbol=symbol, symbols=symbols)

    async def get_rolling_window_ticker(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        window_size: str = "1d",
    ) -> dict:
        """
        Get rolling window price change statistics

        GET /api/v3/ticker
        Weight: 4 per symbol (up to 100 symbols), 200 for 101+ symbols

        Args:
            symbol: 단일 symbol
            symbols: 여러 symbol 리스트
            window_size: Window size (e.g., "1m", "1h", "1d")

        Returns:
            Rolling window ticker data
        """
        await self._check_and_wait(4)
        return self.client.rolling_window_ticker(
            symbol=symbol, symbols=symbols, windowSize=window_size
        )
