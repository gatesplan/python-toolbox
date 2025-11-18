"""
Withdrawals Endpoints Mixin (출금 API)
"""
from typing import Optional


class WithdrawalsMixin:
    """
    Withdrawals endpoints (withdrawals)

    모든 메서드는 BaseThrottler의 _check_and_wait()를 사용
    Withdrawals API는 EXCHANGE_NON_ORDER 카테고리 (초당 30회, 분당 900회)
    """

    async def get_withdraws(
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
        출금 리스트 조회

        GET /v1/withdraws

        Args:
            currency: Currency 코드
            state: 출금 상태 (submitting, submitted, almost_accepted, accepted, processing, done, canceled, rejected)
            uuids: 출금 UUID 리스트
            txids: 출금 TXID 리스트
            limit: 요청 개수 (최대 100)
            page: 페이지 수
            order_by: 정렬 방식 (asc, desc)

        Returns:
            출금 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_withdraws(
            currency=currency,
            state=state,
            uuids=uuids,
            txids=txids,
            limit=limit,
            page=page,
            order_by=order_by,
        )

    async def get_withdraw(
        self,
        uuid: Optional[str] = None,
        txid: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> dict:
        """
        개별 출금 조회

        GET /v1/withdraw

        Args:
            uuid: 출금 UUID
            txid: 출금 TXID
            currency: Currency 코드

        Returns:
            출금 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_withdraw(uuid=uuid, txid=txid, currency=currency)

    async def get_withdraws_chance(self, currency: str) -> dict:
        """
        출금 가능 정보

        GET /v1/withdraws/chance

        Args:
            currency: Currency 코드

        Returns:
            출금 가능 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_withdraws_chance(currency=currency)

    async def withdraw_coin(
        self,
        currency: str,
        amount: str,
        address: str,
        secondary_address: Optional[str] = None,
        transaction_type: str = "default",
    ) -> dict:
        """
        코인 출금하기

        POST /v1/withdraws/coin

        Args:
            currency: Currency 코드
            amount: 출금 코인 수량
            address: 출금 가능 주소
            secondary_address: 2차 주소 (필요한 코인에 한해서)
            transaction_type: 출금 유형 (default, internal)

        Returns:
            출금 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.withdraw_coin(
            currency=currency,
            amount=amount,
            address=address,
            secondary_address=secondary_address,
            transaction_type=transaction_type,
        )

    async def withdraw_krw(self, amount: str) -> dict:
        """
        원화 출금하기

        POST /v1/withdraws/krw

        Args:
            amount: 출금액

        Returns:
            출금 정보
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.withdraw_krw(amount=amount)
