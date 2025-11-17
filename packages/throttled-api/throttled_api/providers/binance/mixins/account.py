"""
Account Endpoints Mixin
"""
from typing import Any, Optional, List


class AccountMixin:
    """
    Account endpoints (account info, orders, trades, etc.)
    """

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[dict]:
        """
        Get all open orders on a symbol or all symbols

        GET /api/v3/openOrders
        Weight: 6 (single symbol), 80 (all symbols)

        Args:
            symbol: Trading pair symbol (optional, if not provided returns all)

        Returns:
            List of open orders
        """
        weight = 6 if symbol else 80
        await self._check_and_wait(weight)
        return await self.client.get_open_orders(symbol=symbol)

    async def get_all_orders(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get all account orders (active, canceled, filled)

        GET /api/v3/allOrders
        Weight: 20

        Args:
            symbol: Trading pair symbol
            order_id: Order ID to fetch from
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Number of orders (default 500, max 1000)

        Returns:
            List of all orders
        """
        await self._check_and_wait(20)
        return await self.client.get_all_orders(
            symbol=symbol,
            orderId=order_id,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )

    async def get_all_order_list(
        self,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get all OCO orders

        GET /api/v3/allOrderList
        Weight: 20

        Args:
            from_id: Order list ID to fetch from
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Number of order lists (default 500, max 1000)

        Returns:
            List of all OCO orders
        """
        await self._check_and_wait(20)
        return await self.client.get_all_order_list(
            fromId=from_id,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )

    async def get_open_order_list(self) -> List[dict]:
        """
        Get open OCO orders

        GET /api/v3/openOrderList
        Weight: 6

        Returns:
            List of open OCO orders
        """
        await self._check_and_wait(6)
        return await self.client.get_open_order_list()

    async def get_my_trades(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get trades for a specific account and symbol

        GET /api/v3/myTrades
        Weight: 20

        Args:
            symbol: Trading pair symbol
            order_id: Filter by order ID
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            from_id: Trade ID to fetch from
            limit: Number of trades (default 500, max 1000)

        Returns:
            List of trades
        """
        await self._check_and_wait(20)
        return await self.client.get_my_trades(
            symbol=symbol,
            orderId=order_id,
            startTime=start_time,
            endTime=end_time,
            fromId=from_id,
            limit=limit,
        )

    async def get_my_allocations(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_allocation_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get allocations for a specific account and symbol

        GET /api/v3/myAllocations
        Weight: 20

        Args:
            symbol: Trading pair symbol
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            from_allocation_id: Allocation ID to fetch from
            limit: Number of allocations (default 500, max 1000)

        Returns:
            List of allocations
        """
        await self._check_and_wait(20)
        return await self.client.get_my_allocations(
            symbol=symbol,
            startTime=start_time,
            endTime=end_time,
            fromAllocationId=from_allocation_id,
            limit=limit,
        )

    async def get_account(self) -> dict:
        """
        Get current account information

        GET /api/v3/account
        Weight: 20

        Returns:
            Account information (balances, permissions, etc.)
        """
        await self._check_and_wait(20)
        return await self.client.get_account()

    async def get_account_commission(self, symbol: str) -> dict:
        """
        Get trade commission rates for a symbol

        GET /api/v3/account/commission
        Weight: 20

        Args:
            symbol: Trading pair symbol

        Returns:
            Commission rates for the symbol
        """
        await self._check_and_wait(20)
        return await self.client.get_account_commission(symbol=symbol)

    async def get_rate_limit_order(self) -> List[dict]:
        """
        Get current order count usage for all intervals

        GET /api/v3/rateLimit/order
        Weight: 40

        Returns:
            Current order rate limit usage
        """
        await self._check_and_wait(40)
        return await self.client.get_rate_limit_order()

    async def get_my_prevented_matches(
        self,
        symbol: str,
        prevent_match_id: Optional[int] = None,
        order_id: Optional[int] = None,
        from_prevent_match_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[dict]:
        """
        Get prevented matches for a symbol

        GET /api/v3/myPreventedMatches
        Weight: 1

        Args:
            symbol: Trading pair symbol
            prevent_match_id: Prevented match ID
            order_id: Order ID
            from_prevent_match_id: Prevented match ID to fetch from
            limit: Number of entries (default 500, max 1000)

        Returns:
            List of prevented matches
        """
        await self._check_and_wait(1)
        return await self.client.get_my_prevented_matches(
            symbol=symbol,
            preventedMatchId=prevent_match_id,
            orderId=order_id,
            fromPreventedMatchId=from_prevent_match_id,
            limit=limit,
        )
