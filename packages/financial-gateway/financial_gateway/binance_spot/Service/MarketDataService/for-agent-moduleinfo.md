# MarketDataService

시장 데이터 및 시스템 정보 조회 Service. 시세, 호가, 캔들, 마켓 목록, 서버 시간을 조회한다.

_request_converter: RequestConverter
_response_parser: ResponseParser
_api_executor: APICallExecutor

__init__(request_converter: RequestConverter, response_parser: ResponseParser, api_executor: APICallExecutor) -> None
    Core 계층 의존성 주입.

get_ticker(request: TickerRequest) -> TickerResponse
    raise BinanceAPIError
    시세 정보 조회.
    1. RequestConverter.convert_ticker_query(request) → API params
    2. APICallExecutor.get_ticker(params) → API response
    3. ResponseParser.parse_ticker_response(response) → TickerResponse

get_orderbook(request: OrderbookRequest) -> OrderbookResponse
    raise BinanceAPIError
    호가 정보 조회.
    1. RequestConverter.convert_orderbook_query(request) → API params
    2. APICallExecutor.get_orderbook(params) → API response
    3. ResponseParser.parse_orderbook_response(response) → OrderbookResponse

get_candles(request: CandleRequest) -> CandleResponse
    raise BinanceAPIError
    캔들 데이터 조회.
    1. RequestConverter.convert_candle_query(request) → API params
    2. APICallExecutor.get_klines(params) → API response
    3. ResponseParser.parse_candle_response(response) → CandleResponse

get_available_markets(request: MarketListRequest) -> MarketListResponse
    raise BinanceAPIError
    거래 가능한 마켓 목록 조회.
    1. APICallExecutor.get_exchange_info() → API response
    2. ResponseParser.parse_market_list_response(response) → MarketListResponse

get_server_time() -> ServerTimeResponse
    raise BinanceAPIError
    서버 시간 조회.
    1. APICallExecutor.get_server_time() → API response
    2. ResponseParser.parse_server_time_response(response) → ServerTimeResponse
