"""
Trading Endpoints Mixin (주문 API)
"""
from typing import Optional, List


class TradingMixin:
    """
    Trading endpoints (orders)

    주문 생성/취소는 EXCHANGE_ORDER 카테고리 (초당 8회, 분당 200회)
    주문 조회는 EXCHANGE_NON_ORDER 카테고리 (초당 30회, 분당 900회)
    """

    async def create_order(
        self,
        market: str,
        side: str,
        ord_type: str,
        volume: Optional[str] = None,
        price: Optional[str] = None,
        identifier: Optional[str] = None,
    ) -> dict:
        """
        주문하기

        POST /v1/orders
        주문 요청 (초당 8회, 분당 200회 제한)

        Args:
            market: 마켓 ID (예: KRW-BTC)
            side: 주문 종류 (bid: 매수, ask: 매도)
            ord_type: 주문 타입 (limit: 지정가, price: 시장가 매수, market: 시장가 매도)
            volume: 주문량 (지정가, 시장가 매도 시 필수)
            price: 주문 가격 (지정가, 시장가 매수 시 필수)
            identifier: 조회용 사용자 지정 값

        Returns:
            주문 결과
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_ORDER")
        return await self.client.create_order(
            market=market,
            side=side,
            ord_type=ord_type,
            volume=volume,
            price=price,
            identifier=identifier,
        )

    async def cancel_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> dict:
        """
        주문 취소

        DELETE /v1/order
        주문 취소 요청 (초당 8회, 분당 200회 제한)

        Args:
            uuid: 주문 UUID
            identifier: 조회용 사용자 지정 값

        Returns:
            취소 결과
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_ORDER")
        return await self.client.cancel_order(uuid=uuid, identifier=identifier)

    async def get_order(
        self,
        uuid: Optional[str] = None,
        identifier: Optional[str] = None,
    ) -> dict:
        """
        개별 주문 조회

        GET /v1/order

        Args:
            uuid: 주문 UUID
            identifier: 조회용 사용자 지정 값

        Returns:
            주문 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_order(uuid=uuid, identifier=identifier)

    async def get_orders(
        self,
        market: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None,
        state: Optional[str] = None,
        states: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "desc",
    ) -> list:
        """
        주문 리스트 조회

        GET /v1/orders

        Args:
            market: 마켓 ID
            uuids: 주문 UUID 리스트
            identifiers: 주문 identifier 리스트
            state: 주문 상태 (wait, watch, done, cancel)
            states: 주문 상태 리스트
            page: 페이지 수
            limit: 요청 개수 (최대 100)
            order_by: 정렬 방식 (asc, desc)

        Returns:
            주문 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_orders(
            market=market,
            uuids=uuids,
            identifiers=identifiers,
            state=state,
            states=states,
            page=page,
            limit=limit,
            order_by=order_by,
        )

    async def get_orders_chance(self, market: str) -> dict:
        """
        주문 가능 정보

        GET /v1/orders/chance
        마켓별 주문 가능 정보 확인

        Args:
            market: 마켓 ID

        Returns:
            주문 가능 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_orders_chance(market=market)

    async def get_orders_open(
        self,
        market: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "desc",
    ) -> list:
        """
        미체결 주문 조회

        GET /v1/orders/open

        Args:
            market: 마켓 ID
            page: 페이지 수
            limit: 요청 개수 (최대 100)
            order_by: 정렬 방식

        Returns:
            미체결 주문 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_orders_open(
            market=market, page=page, limit=limit, order_by=order_by
        )

    async def get_orders_closed(
        self,
        market: Optional[str] = None,
        state: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "desc",
    ) -> list:
        """
        종료된 주문 조회

        GET /v1/orders/closed

        Args:
            market: 마켓 ID
            state: 주문 상태 (done, cancel)
            start_time: 시작 시간
            end_time: 종료 시간
            page: 페이지 수
            limit: 요청 개수 (최대 100)
            order_by: 정렬 방식

        Returns:
            종료된 주문 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_orders_closed(
            market=market,
            state=state,
            start_time=start_time,
            end_time=end_time,
            page=page,
            limit=limit,
            order_by=order_by,
        )
