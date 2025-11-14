# OrderQueryService

주문 조회 및 관리 Service. 주문 취소, 상태 조회, 체결 내역 조회를 담당한다.

_request_converter: RequestConverter
_response_parser: ResponseParser
_api_executor: APICallExecutor

__init__(request_converter: RequestConverter, response_parser: ResponseParser, api_executor: APICallExecutor) -> None
    Core 계층 의존성 주입.

cancel_order(request: CancelOrderRequest) -> CancelOrderResponse
    raise BinanceAPIError, ValidationError
    주문 취소 실행.
    1. RequestConverter.convert_cancel_order(request) → API params
    2. APICallExecutor.cancel_order(params) → API response
    3. ResponseParser.parse_cancel_response(response) → CancelOrderResponse

get_order_status(request: OrderStatusRequest) -> OrderStatusResponse
    raise BinanceAPIError, ValidationError
    주문 상태 조회.
    1. RequestConverter.convert_order_status_query(request) → API params
    2. APICallExecutor.query_order(params) → API response
    3. ResponseParser.parse_order_status_response(response) → OrderStatusResponse

get_trade_history(request: TradeHistoryRequest) -> TradeHistoryResponse
    raise BinanceAPIError, ValidationError
    체결 내역 조회.
    1. RequestConverter.convert_trade_history_query(request) → API params
    2. APICallExecutor.query_trades(params) → API response
    3. ResponseParser.parse_trade_history_response(response) → TradeHistoryResponse
