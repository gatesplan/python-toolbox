"""
Trading Endpoints Mixin
"""
from typing import Any, Optional, List


class TradingMixin:
    """
    Trading endpoints (order, orderList, SOR)
    """

    async def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        **kwargs,
    ) -> dict:
        """
        Create a new order

        POST /api/v3/order
        Weight: 1

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            side: Order side (BUY or SELL)
            type: Order type (LIMIT, MARKET, STOP_LOSS, etc.)
            **kwargs: Additional order parameters (timeInForce, quantity, price, etc.)

        Returns:
            Order creation response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.new_order(symbol=symbol, side=side, type=type, **kwargs)

    async def test_order(
        self,
        symbol: str,
        side: str,
        type: str,
        **kwargs,
    ) -> dict:
        """
        Test order creation without actually placing the order

        POST /api/v3/order/test
        Weight: 1

        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            type: Order type
            **kwargs: Additional order parameters

        Returns:
            Test result (empty dict if valid)
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.new_order_test(symbol=symbol, side=side, type=type, **kwargs)

    async def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> dict:
        """
        Query order status

        GET /api/v3/order
        Weight: 4

        Args:
            symbol: Trading pair symbol
            order_id: Order ID (either orderId or origClientOrderId must be provided)
            orig_client_order_id: Original client order ID

        Returns:
            Order information
        """
        await self._check_and_wait(4)
        return self.client.get_order(
            symbol=symbol,
            orderId=order_id,
            origClientOrderId=orig_client_order_id,
        )

    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Cancel an active order

        DELETE /api/v3/order
        Weight: 1

        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            orig_client_order_id: Original client order ID
            **kwargs: Additional cancel parameters

        Returns:
            Cancelled order information
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.cancel_order(
            symbol=symbol,
            orderId=order_id,
            origClientOrderId=orig_client_order_id,
            **kwargs,
        )

    async def cancel_open_orders(self, symbol: str) -> List[dict]:
        """
        Cancel all open orders on a symbol

        DELETE /api/v3/openOrders
        Weight: 1

        Args:
            symbol: Trading pair symbol

        Returns:
            List of cancelled orders
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.cancel_open_orders(symbol=symbol)

    async def cancel_replace_order(
        self,
        symbol: str,
        cancel_replace_mode: str,
        side: str,
        type: str,
        **kwargs,
    ) -> dict:
        """
        Cancel an existing order and place a new order

        POST /api/v3/order/cancelReplace
        Weight: 1

        Args:
            symbol: Trading pair symbol
            cancel_replace_mode: STOP_ON_FAILURE or ALLOW_FAILURE
            side: Order side (BUY or SELL)
            type: Order type
            **kwargs: Additional parameters (cancelOrderId, quantity, price, etc.)

        Returns:
            Cancel and new order response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.cancel_and_replace(
            symbol=symbol,
            cancelReplaceMode=cancel_replace_mode,
            side=side,
            type=type,
            **kwargs,
        )

    async def create_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        above_type: str,
        below_type: str,
        **kwargs,
    ) -> dict:
        """
        Create OCO (One-Cancels-the-Other) order

        POST /api/v3/orderList/oco
        Weight: 1

        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            above_type: Above order type (e.g., "LIMIT_MAKER")
            below_type: Below order type (e.g., "STOP_LOSS_LIMIT")
            **kwargs: Additional OCO parameters (price, stopPrice, belowPrice, etc.)

        Returns:
            OCO order creation response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.new_oco_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            aboveType=above_type,
            belowType=below_type,
            **kwargs,
        )

    async def create_oto_order(
        self,
        symbol: str,
        working_type: str,
        working_side: str,
        working_price: float,
        working_quantity: float,
        pending_type: str,
        pending_side: str,
        **kwargs,
    ) -> dict:
        """
        Create OTO (One-Triggers-the-Other) order

        POST /api/v3/orderList/oto
        Weight: 1

        Args:
            symbol: Trading pair symbol
            working_type: Working order type
            working_side: Working order side
            working_price: Working order price
            working_quantity: Working order quantity
            pending_type: Pending order type
            pending_side: Pending order side
            **kwargs: Additional OTO parameters

        Returns:
            OTO order creation response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.new_oto_order(
            symbol=symbol,
            workingType=working_type,
            workingSide=working_side,
            workingPrice=working_price,
            workingQuantity=working_quantity,
            pendingType=pending_type,
            pendingSide=pending_side,
            **kwargs,
        )

    async def create_otoco_order(
        self,
        symbol: str,
        working_type: str,
        working_side: str,
        working_price: float,
        working_quantity: float,
        pending_side: str,
        pending_quantity: float,
        pending_above_type: str,
        **kwargs,
    ) -> dict:
        """
        Create OTOCO (One-Triggers-One-Cancels-the-Other) order

        POST /api/v3/orderList/otoco
        Weight: 1

        Args:
            symbol: Trading pair symbol
            working_type: Working order type
            working_side: Working order side
            working_price: Working order price
            working_quantity: Working order quantity
            pending_side: Pending order side
            pending_quantity: Pending order quantity
            pending_above_type: Pending above order type
            **kwargs: Additional OTOCO parameters

        Returns:
            OTOCO order creation response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.new_otoco_order(
            symbol=symbol,
            workingType=working_type,
            workingSide=working_side,
            workingPrice=working_price,
            workingQuantity=working_quantity,
            pendingSide=pending_side,
            pendingQuantity=pending_quantity,
            pendingAboveType=pending_above_type,
            **kwargs,
        )

    async def cancel_order_list(
        self,
        symbol: str,
        order_list_id: Optional[int] = None,
        list_client_order_id: Optional[str] = None,
    ) -> dict:
        """
        Cancel an entire order list

        DELETE /api/v3/orderList
        Weight: 1

        Args:
            symbol: Trading pair symbol
            order_list_id: Order list ID
            list_client_order_id: List client order ID

        Returns:
            Cancelled order list information
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.cancel_order_list(
            symbol=symbol,
            orderListId=order_list_id,
            listClientOrderId=list_client_order_id,
        )

    async def get_order_list(
        self,
        order_list_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> dict:
        """
        Query order list status

        GET /api/v3/orderList
        Weight: 4

        Args:
            order_list_id: Order list ID
            orig_client_order_id: Original client order ID

        Returns:
            Order list information
        """
        await self._check_and_wait(4)
        return self.client.get_order_list(
            orderListId=order_list_id,
            origClientOrderId=orig_client_order_id,
        )

    async def create_sor_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float,
        **kwargs,
    ) -> dict:
        """
        Create SOR (Smart Order Routing) order

        POST /api/v3/sor/order
        Weight: 1

        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            type: Order type
            quantity: Order quantity
            **kwargs: Additional SOR parameters

        Returns:
            SOR order creation response
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.create_sor_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            **kwargs,
        )

    async def test_sor_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float,
        **kwargs,
    ) -> dict:
        """
        Test SOR order creation without placing the order

        POST /api/v3/sor/order/test
        Weight: 1

        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            type: Order type
            quantity: Order quantity
            **kwargs: Additional SOR parameters

        Returns:
            Test result (empty dict if valid)
        """
        await self._check_and_wait(1)
        await self._check_orders(1)
        return self.client.test_sor_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            **kwargs,
        )
