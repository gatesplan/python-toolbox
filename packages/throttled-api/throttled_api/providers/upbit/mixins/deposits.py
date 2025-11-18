"""
Deposits Endpoints Mixin (입금 API)
"""
from typing import Optional


class DepositsMixin:
    """
    Deposits endpoints (deposits, deposit addresses)

    모든 메서드는 BaseThrottler의 _check_and_wait()를 사용
    Deposits API는 EXCHANGE_NON_ORDER 카테고리 (초당 30회, 분당 900회)
    """

    async def get_deposits(
        self,
        currency: Optional[str] = None,
        state: Optional[str] = None,
        uuids: Optional[list] = None,
        txids: Optional[list] = None,
        limit: int = 100,
        page: int = 1,
        order_by: str = "desc",
    ) -> list:
        """
        입금 리스트 조회

        GET /v1/deposits

        Args:
            currency: Currency 코드
            state: 입금 상태 (submitting, submitted, almost_accepted, accepted, processing, done, canceled, rejected)
            uuids: 입금 UUID 리스트
            txids: 입금 TXID 리스트
            limit: 요청 개수 (최대 100)
            page: 페이지 수
            order_by: 정렬 방식 (asc, desc)

        Returns:
            입금 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_deposits(
            currency=currency,
            state=state,
            uuids=uuids,
            txids=txids,
            limit=limit,
            page=page,
            order_by=order_by,
        )

    async def get_deposit(
        self,
        uuid: Optional[str] = None,
        txid: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> dict:
        """
        개별 입금 조회

        GET /v1/deposit

        Args:
            uuid: 입금 UUID
            txid: 입금 TXID
            currency: Currency 코드

        Returns:
            입금 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_deposit(uuid=uuid, txid=txid, currency=currency)

    async def generate_coin_address(self, currency: str) -> dict:
        """
        입금 주소 생성 요청

        POST /v1/deposits/generate_coin_address

        Args:
            currency: Currency 코드

        Returns:
            입금 주소 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.generate_coin_address(currency=currency)

    async def get_coin_addresses(self) -> list:
        """
        전체 입금 주소 조회

        GET /v1/deposits/coin_addresses

        Returns:
            입금 주소 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_coin_addresses()

    async def get_coin_address(self, currency: str) -> dict:
        """
        개별 입금 주소 조회

        GET /v1/deposits/coin_address

        Args:
            currency: Currency 코드

        Returns:
            입금 주소 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_coin_address(currency=currency)

    async def create_krw_deposit(self, amount: str) -> dict:
        """
        원화 입금하기

        POST /v1/deposits/krw

        Args:
            amount: 입금액

        Returns:
            입금 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.create_krw_deposit(amount=amount)
