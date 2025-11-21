"""
Upbit Client Adapter

upbit-client 패키지의 동기 API를 UpbitSpotThrottler가 기대하는 비동기 API로 변환
"""
import json
from typing import Optional, List, Any
from upbit.client import Upbit


class UpbitClientAdapter:
    """
    upbit-client의 동기 API를 비동기 API로 변환하는 어댑터

    UpbitSpotThrottler는 client.get_market_all() 같은 flat한 비동기 API를 기대하지만,
    upbit-client는 client.Market.Market_info_all() 같은 계층 구조의 동기 API를 제공합니다.

    upbit-client는 response['text']에 JSON 문자열을 반환하므로, 파싱하여 반환합니다.
    """

    def __init__(self, access_key: str, secret_key: str):
        self._client = Upbit(access_key=access_key, secret_key=secret_key)

    def _parse_response(self, response: dict) -> Any:
        """upbit-client 응답을 파싱"""
        # upbit-client는 두 가지 응답 형식을 반환:
        # 1. dict with 'response' key (bravado format)
        # 2. dict with 'text' key (raw format)
        if isinstance(response, dict):
            if 'response' in response and isinstance(response['response'], dict):
                # bravado format - 'text' 필드를 JSON 파싱
                if 'text' in response['response']:
                    return json.loads(response['response']['text'])
            elif 'text' in response:
                # raw format
                return json.loads(response['text'])
        return response

    # Quotation API (Market)
    async def get_market_all(self, is_details: bool = False) -> List[dict]:
        """마켓 코드 조회"""
        response = self._client.Market.Market_info_all(isDetails=is_details)
        return self._parse_response(response)

    # Quotation API (Candle)
    async def get_candles_minutes(
        self,
        unit: int,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> List[dict]:
        """분 캔들 조회"""
        response = self._client.Candle.Candle_minutes(
            unit=unit, market=market, to=to, count=count
        )
        return self._parse_response(response)

    async def get_candles_days(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        converting_price_unit: Optional[str] = None,
    ) -> List[dict]:
        """일 캔들 조회"""
        response = self._client.Candle.Candle_days(
            market=market, to=to, count=count, convertingPriceUnit=converting_price_unit
        )
        return self._parse_response(response)

    async def get_candles_weeks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> List[dict]:
        """주 캔들 조회"""
        response = self._client.Candle.Candle_weeks(
            market=market, to=to, count=count
        )
        return self._parse_response(response)

    async def get_candles_months(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
    ) -> List[dict]:
        """월 캔들 조회"""
        response = self._client.Candle.Candle_month(
            market=market, to=to, count=count
        )
        return self._parse_response(response)

    # Quotation API (Orderbook, Ticker, Trades)
    async def get_ticker(self, markets: List[str]) -> List[dict]:
        """현재가 정보 조회"""
        # Upbit API는 markets를 comma-separated string으로 받음
        markets_str = ','.join(markets) if isinstance(markets, list) else markets
        response = self._client.Trade.Trade_ticker(markets=markets_str)
        return self._parse_response(response)

    async def get_orderbook(self, markets: List[str]) -> List[dict]:
        """호가 정보 조회"""
        # Upbit orderbook은 list를 받음
        response = self._client.Order.Order_orderbook(markets=markets)
        return self._parse_response(response)

    async def get_trades_ticks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        cursor: Optional[str] = None,
        days_ago: Optional[int] = None,
    ) -> List[dict]:
        """최근 체결 내역 조회"""
        response = self._client.Trade.Trade_tick(
            market=market, to=to, count=count, cursor=cursor, daysAgo=days_ago
        )
        return self._parse_response(response)

    # Account API
    async def get_accounts(self) -> List[dict]:
        """전체 계좌 조회"""
        response = self._client.Account.Account_info()
        return self._parse_response(response)

    async def get_api_keys(self) -> List[dict]:
        """API 키 리스트 조회"""
        response = self._client.APIKey.APIKey_info()
        return self._parse_response(response)

    # Trading API (Order)
    async def create_order(
        self,
        market: str,
        side: str,
        volume: Optional[str] = None,
        price: Optional[str] = None,
        ord_type: str = "limit",
        identifier: Optional[str] = None,
    ) -> dict:
        """주문하기"""
        response = self._client.Order.Order_new(
            market=market,
            side=side,
            volume=volume,
            price=price,
            ord_type=ord_type,
            identifier=identifier,
        )
        return self._parse_response(response)

    async def cancel_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> dict:
        """주문 취소"""
        response = self._client.Order.Order_cancel(uuid=uuid, identifier=identifier)
        return self._parse_response(response)

    async def get_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> dict:
        """개별 주문 조회"""
        response = self._client.Order.Order_info(uuid=uuid, identifier=identifier)
        return self._parse_response(response)

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
    ) -> List[dict]:
        """주문 리스트 조회"""
        response = self._client.Order.Order_info_all(
            market=market,
            uuids=uuids,
            identifiers=identifiers,
            state=state,
            states=states,
            page=page,
            limit=limit,
            order_by=order_by,
        )
        return self._parse_response(response)

    async def get_orders_chance(self, market: str) -> dict:
        """주문 가능 정보"""
        response = self._client.Order.Order_chance(market=market)
        return self._parse_response(response)

    async def get_orders_open(
        self,
        market: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "desc",
    ) -> List[dict]:
        """미체결 주문 조회"""
        response = self._client.Order.Order_info_all(
            market=market, state="wait", page=page, limit=limit, order_by=order_by
        )
        return self._parse_response(response)

    async def get_orders_closed(
        self,
        market: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "desc",
    ) -> List[dict]:
        """체결 완료 주문 조회"""
        response = self._client.Order.Order_info_all(
            market=market, state="done", page=page, limit=limit, order_by=order_by
        )
        return self._parse_response(response)

    # Deposits API
    async def get_deposits(
        self,
        currency: Optional[str] = None,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        limit: int = 100,
        page: int = 1,
        order_by: str = "desc",
    ) -> List[dict]:
        """입금 리스트 조회"""
        response = self._client.Deposit.Deposit_info_all(
            currency=currency,
            state=state,
            uuids=uuids,
            txids=txids,
            limit=limit,
            page=page,
            order_by=order_by,
        )
        return self._parse_response(response)

    async def get_deposit(self, uuid: Optional[str] = None, txid: Optional[str] = None, currency: Optional[str] = None) -> dict:
        """개별 입금 조회"""
        response = self._client.Deposit.Deposit_info(uuid=uuid, txid=txid, currency=currency)
        return self._parse_response(response)

    async def generate_coin_address(self, currency: str) -> dict:
        """입금 주소 생성"""
        response = self._client.Deposit.Deposit_generate_coin_address(currency=currency)
        return self._parse_response(response)

    async def get_coin_addresses(self) -> List[dict]:
        """전체 입금 주소 조회"""
        response = self._client.Deposit.Deposit_coin_addresses()
        return self._parse_response(response)

    async def get_coin_address(self, currency: str) -> dict:
        """개별 입금 주소 조회"""
        response = self._client.Deposit.Deposit_coin_address(currency=currency)
        return self._parse_response(response)

    async def create_krw_deposit(self, amount: str) -> dict:
        """원화 입금하기"""
        response = self._client.Deposit.Deposit_krw(amount=amount)
        return self._parse_response(response)

    # Withdrawals API
    async def get_withdraws(
        self,
        currency: Optional[str] = None,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        limit: int = 100,
        page: int = 1,
        order_by: str = "desc",
    ) -> List[dict]:
        """출금 리스트 조회"""
        response = self._client.Withdraw.Withdraw_info_all(
            currency=currency,
            state=state,
            uuids=uuids,
            txids=txids,
            limit=limit,
            page=page,
            order_by=order_by,
        )
        return self._parse_response(response)

    async def get_withdraw(self, uuid: Optional[str] = None, txid: Optional[str] = None, currency: Optional[str] = None) -> dict:
        """개별 출금 조회"""
        response = self._client.Withdraw.Withdraw_info(uuid=uuid, txid=txid, currency=currency)
        return self._parse_response(response)

    async def get_withdraws_chance(self, currency: str) -> dict:
        """출금 가능 정보"""
        response = self._client.Withdraw.Withdraw_chance(currency=currency)
        return self._parse_response(response)

    async def withdraw_coin(
        self,
        currency: str,
        amount: str,
        address: str,
        secondary_address: Optional[str] = None,
        transaction_type: str = "default",
    ) -> dict:
        """코인 출금하기"""
        response = self._client.Withdraw.Withdraw_coin(
            currency=currency,
            amount=amount,
            address=address,
            secondary_address=secondary_address,
            transaction_type=transaction_type,
        )
        return self._parse_response(response)

    async def withdraw_krw(self, amount: str) -> dict:
        """원화 출금하기"""
        response = self._client.Withdraw.Withdraw_krw(amount=amount)
        return self._parse_response(response)
