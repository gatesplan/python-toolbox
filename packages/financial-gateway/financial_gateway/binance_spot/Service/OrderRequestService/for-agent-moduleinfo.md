# OrderRequestService

주문 요청 처리 Service. Request 객체를 받아 Binance API를 호출하고 Response를 반환한다.

_request_converter: RequestConverter
_response_parser: ResponseParser
_api_executor: APICallExecutor

__init__(request_converter: RequestConverter, response_parser: ResponseParser, api_executor: APICallExecutor) -> None
    Core 계층 의존성 주입.

execute_limit_buy(request: LimitBuyOrderRequest) -> OpenSpotOrderResponse
    raise BinanceAPIError, ValidationError
    지정가 매수 주문 실행.
    1. RequestConverter.convert_limit_buy(request) → API params
    2. APICallExecutor.place_order(params) → API response
    3. ResponseParser.parse_order_response(response) → OpenSpotOrderResponse

execute_limit_sell(request: LimitSellOrderRequest) -> OpenSpotOrderResponse
    raise BinanceAPIError, ValidationError
    지정가 매도 주문 실행.

execute_market_buy(request: MarketBuyOrderRequest) -> OpenSpotOrderResponse
    raise BinanceAPIError, ValidationError
    시장가 매수 주문 실행.

execute_market_sell(request: MarketSellOrderRequest) -> OpenSpotOrderResponse
    raise BinanceAPIError, ValidationError
    시장가 매도 주문 실행.

## 워크플로우

```python
# 1. Request → API params
params = self._request_converter.convert_limit_buy(request)
# params = {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "price": 50000.0, "quantity": 0.001}

# 2. API 호출
api_response = self._api_executor.place_order(params)
# api_response = {"orderId": 123, "status": "NEW", ...}

# 3. API response → Response
response = self._response_parser.parse_order_response(api_response)
# response = OpenSpotOrderResponse(is_success=True, order=SpotOrder(...))
```
