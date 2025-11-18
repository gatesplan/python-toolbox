"""
Quotation Endpoints Mixin (시세 조회 API)
"""
from typing import Optional, List


class QuotationMixin:
    """
    Quotation endpoints (market data, candles, ticker, orderbook, trades)

    모든 메서드는 BaseThrottler의 _check_and_wait()를 사용
    Quotation API는 인증이 필요 없으며, 초당 10회, 분당 600회 제한
    """

    async def get_market_all(self, is_details: bool = False) -> dict:
        """
        마켓 코드 조회

        GET /v1/market/all
        업비트에서 거래 가능한 마켓 목록

        Args:
            is_details: 유의종목 필드와 같은 상세 정보 포함 여부

        Returns:
            마켓 목록
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_market_all(is_details=is_details)

    async def get_candles_minutes(
        self,
        unit: int,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> list:
        """
        분(Minute) 캔들 조회

        GET /v1/candles/minutes/{unit}

        Args:
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            market: 마켓 코드 (예: KRW-BTC)
            to: 마지막 캔들 시각 (yyyy-MM-dd'T'HH:mm:ss'Z' 또는 yyyy-MM-dd HH:mm:ss), 빈 값이면 현재 시각
            count: 캔들 개수 (최대 200)

        Returns:
            캔들 데이터 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_candles_minutes(
            unit=unit, market=market, to=to, count=count
        )

    async def get_candles_days(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        converting_price_unit: Optional[str] = None,
    ) -> list:
        """
        일(Day) 캔들 조회

        GET /v1/candles/days

        Args:
            market: 마켓 코드
            to: 마지막 캔들 시각
            count: 캔들 개수 (최대 200)
            converting_price_unit: 종가 환산 화폐 단위 (KRW로 명시할 시 원화 환산 가격 반환)

        Returns:
            캔들 데이터 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_candles_days(
            market=market,
            to=to,
            count=count,
            converting_price_unit=converting_price_unit,
        )

    async def get_candles_weeks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> list:
        """
        주(Week) 캔들 조회

        GET /v1/candles/weeks

        Args:
            market: 마켓 코드
            to: 마지막 캔들 시각
            count: 캔들 개수 (최대 200)

        Returns:
            캔들 데이터 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_candles_weeks(market=market, to=to, count=count)

    async def get_candles_months(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> list:
        """
        월(Month) 캔들 조회

        GET /v1/candles/months

        Args:
            market: 마켓 코드
            to: 마지막 캔들 시각
            count: 캔들 개수 (최대 200)

        Returns:
            캔들 데이터 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_candles_months(market=market, to=to, count=count)

    async def get_ticker(self, markets: List[str]) -> list:
        """
        현재가 정보 조회

        GET /v1/ticker
        요청 당시 종목의 스냅샷

        Args:
            markets: 마켓 코드 리스트 (예: ["KRW-BTC", "KRW-ETH"])

        Returns:
            현재가 정보 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_ticker(markets=markets)

    async def get_orderbook(self, markets: List[str]) -> list:
        """
        호가 정보 조회

        GET /v1/orderbook

        Args:
            markets: 마켓 코드 리스트 (예: ["KRW-BTC"])

        Returns:
            호가 정보 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_orderbook(markets=markets)

    async def get_trades_ticks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        cursor: Optional[str] = None,
        days_ago: Optional[int] = None,
    ) -> list:
        """
        최근 체결 내역 조회

        GET /v1/trades/ticks

        Args:
            market: 마켓 코드
            to: 마지막 체결 시각 (HHmmss 또는 HH:mm:ss)
            count: 체결 개수 (최대 500)
            cursor: 페이지네이션 커서
            days_ago: 최근 체결 날짜 기준 7일 이내의 이전 데이터 조회 가능 (범위: 1 ~ 7)

        Returns:
            체결 내역 리스트
        """
        await self._check_and_wait(cost=1, category="QUOTATION")
        return await self.client.get_trades_ticks(
            market=market, to=to, count=count, cursor=cursor, days_ago=days_ago
        )
