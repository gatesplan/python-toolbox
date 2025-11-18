"""
Account Endpoints Mixin (계좌 API)
"""
from typing import Optional


class AccountMixin:
    """
    Account endpoints (accounts, api_keys)

    모든 메서드는 BaseThrottler의 _check_and_wait()를 사용
    Account API는 EXCHANGE_NON_ORDER 카테고리 (초당 30회, 분당 900회)
    """

    async def get_accounts(self) -> list:
        """
        전체 계좌 조회

        GET /v1/accounts
        내가 보유한 자산 리스트 조회

        Returns:
            계좌 목록
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_accounts()

    async def get_api_keys(self) -> list:
        """
        API 키 리스트 조회

        GET /v1/api_keys
        API 키 목록 및 만료 일자 조회

        Returns:
            API 키 정보 리스트
        """
        await self._check_and_wait(cost=1, category="EXCHANGE_NON_ORDER")
        return await self.client.get_api_keys()
