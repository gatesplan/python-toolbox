# Core 계층

순수 변환/파싱/API 호출 로직을 담당한다. Stateless로 설계되어 재사용성이 높다.

## RequestConverter
Request 객체를 Binance API 파라미터로 변환하는 순수 변환 로직.

convert_limit_buy(request: LimitBuyOrderRequest) -> dict
    LimitBuyOrderRequest → {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", ...}

convert_limit_sell(request: LimitSellOrderRequest) -> dict
    LimitSellOrderRequest → {"symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT", ...}

convert_market_buy(request: MarketBuyOrderRequest) -> dict
    MarketBuyOrderRequest → {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", ...}

convert_market_sell(request: MarketSellOrderRequest) -> dict
    MarketSellOrderRequest → {"symbol": "BTCUSDT", "side": "SELL", "type": "MARKET", ...}

convert_cancel_order(request: CancelOrderRequest) -> dict
    CancelOrderRequest → {"symbol": "BTCUSDT", "orderId": 123}

convert_order_status_query(request: OrderStatusRequest) -> dict
    OrderStatusRequest → {"symbol": "BTCUSDT", "orderId": 123}

convert_ticker_query(request: TickerRequest) -> dict
    TickerRequest → {"symbol": "BTCUSDT"}

convert_orderbook_query(request: OrderbookRequest) -> dict
    OrderbookRequest → {"symbol": "BTCUSDT", "limit": 100}

convert_candle_query(request: CandleRequest) -> dict
    CandleRequest → {"symbol": "BTCUSDT", "interval": "1h", "limit": 500}

## ResponseParser
Binance API 응답을 Response 객체로 파싱하는 순수 파싱 로직.

parse_order_response(api_response: dict) -> OpenSpotOrderResponse
    Binance 주문 응답 → OpenSpotOrderResponse

parse_cancel_response(api_response: dict) -> CancelOrderResponse
    Binance 취소 응답 → CancelOrderResponse

parse_order_status_response(api_response: dict) -> OrderStatusResponse
    Binance 주문 상태 응답 → OrderStatusResponse

parse_trade_history_response(api_response: dict) -> TradeHistoryResponse
    Binance 체결 내역 응답 → TradeHistoryResponse

parse_balance_response(api_response: dict) -> BalanceResponse
    Binance 계정 정보 응답 → BalanceResponse

parse_ticker_response(api_response: dict) -> TickerResponse
    Binance 시세 응답 → TickerResponse

parse_orderbook_response(api_response: dict) -> OrderbookResponse
    Binance 호가 응답 → OrderbookResponse

parse_candle_response(api_response: list) -> CandleResponse
    Binance K선 응답 → CandleResponse

parse_market_list_response(api_response: dict) -> MarketListResponse
    Binance 거래소 정보 응답 → MarketListResponse

parse_server_time_response(api_response: dict) -> ServerTimeResponse
    Binance 서버 시간 응답 → ServerTimeResponse

## APICallExecutor
binance-connector 라이브러리를 사용하여 실제 API를 호출한다.

_client: Spot    # binance.spot.Spot 클라이언트
api_key: str
api_secret: str

__init__(api_key: str, api_secret: str) -> None
    binance-connector Spot 클라이언트 초기화.

place_order(params: dict) -> dict
    raise BinanceAPIError
    주문 생성 API 호출. POST /api/v3/order

cancel_order(params: dict) -> dict
    raise BinanceAPIError
    주문 취소 API 호출. DELETE /api/v3/order

query_order(params: dict) -> dict
    raise BinanceAPIError
    주문 조회 API 호출. GET /api/v3/order

query_trades(params: dict) -> dict
    raise BinanceAPIError
    체결 내역 조회 API 호출. GET /api/v3/myTrades

get_account_info() -> dict
    raise BinanceAPIError
    계정 정보 조회 API 호출. GET /api/v3/account

get_ticker(params: dict) -> dict
    raise BinanceAPIError
    시세 정보 조회 API 호출. GET /api/v3/ticker/24hr

get_orderbook(params: dict) -> dict
    raise BinanceAPIError
    호가 정보 조회 API 호출. GET /api/v3/depth

get_klines(params: dict) -> list
    raise BinanceAPIError
    K선(캔들) 데이터 조회 API 호출. GET /api/v3/klines

get_exchange_info() -> dict
    raise BinanceAPIError
    거래소 정보 조회 API 호출. GET /api/v3/exchangeInfo

get_server_time() -> dict
    raise BinanceAPIError
    서버 시간 조회 API 호출. GET /api/v3/time
