# APICallExecutor

binance-connector 라이브러리를 사용하여 실제 Binance API를 호출한다.

_client: Spot    # binance.spot.Spot 인스턴스
api_key: str
api_secret: str

__init__(api_key: str, api_secret: str) -> None
    Binance Spot 클라이언트 초기화.
    from binance.spot import Spot
    self._client = Spot(api_key=api_key, api_secret=api_secret)

## 주문 관련 API

place_order(params: dict) -> dict
    raise BinanceAPIError
    주문 생성 API 호출.
    return self._client.new_order(**params)
    POST /api/v3/order

cancel_order(params: dict) -> dict
    raise BinanceAPIError
    주문 취소 API 호출.
    return self._client.cancel_order(**params)
    DELETE /api/v3/order

query_order(params: dict) -> dict
    raise BinanceAPIError
    주문 상태 조회 API 호출.
    return self._client.get_order(**params)
    GET /api/v3/order

query_trades(params: dict) -> list
    raise BinanceAPIError
    계정 체결 내역 조회 API 호출.
    return self._client.my_trades(**params)
    GET /api/v3/myTrades

## 계정 정보 API

get_account_info() -> dict
    raise BinanceAPIError
    계정 정보 조회 API 호출.
    return self._client.account()
    GET /api/v3/account

## 시장 데이터 API (Public)

get_ticker(params: dict) -> dict
    raise BinanceAPIError
    24시간 시세 정보 조회 API 호출.
    return self._client.ticker_24hr(**params)
    GET /api/v3/ticker/24hr

get_orderbook(params: dict) -> dict
    raise BinanceAPIError
    호가 정보 조회 API 호출.
    return self._client.depth(**params)
    GET /api/v3/depth

get_klines(params: dict) -> list
    raise BinanceAPIError
    K선(캔들) 데이터 조회 API 호출.
    return self._client.klines(**params)
    GET /api/v3/klines

get_exchange_info() -> dict
    raise BinanceAPIError
    거래소 정보 조회 API 호출.
    return self._client.exchange_info()
    GET /api/v3/exchangeInfo

get_server_time() -> dict
    raise BinanceAPIError
    서버 시간 조회 API 호출.
    return self._client.time()
    GET /api/v3/time

## 에러 핸들링

모든 메서드는 binance-connector의 예외를 catch하여 BinanceAPIError로 변환하여 재발생시킨다.
