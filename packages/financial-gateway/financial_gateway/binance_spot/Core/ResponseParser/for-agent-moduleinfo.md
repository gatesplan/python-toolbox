# ResponseParser

Binance API 응답(dict/list)을 Response 객체로 파싱하는 순수 파싱 로직. 모든 메서드는 정적 메서드로 Stateless하게 동작한다.

## 주문 응답 파싱

@staticmethod
parse_order_response(api_response: dict) -> OpenSpotOrderResponse
    Binance 주문 생성 응답 → OpenSpotOrderResponse.
    api_response = {"orderId": 123, "symbol": "BTCUSDT", "status": "NEW", "price": "50000.0", ...}
    SpotOrder 객체 생성 후 OpenSpotOrderResponse로 래핑.

@staticmethod
parse_cancel_response(api_response: dict) -> CancelOrderResponse
    Binance 주문 취소 응답 → CancelOrderResponse.
    api_response = {"orderId": 123, "status": "CANCELED", ...}

@staticmethod
parse_order_status_response(api_response: dict) -> OrderStatusResponse
    Binance 주문 상태 조회 응답 → OrderStatusResponse.
    api_response = {"orderId": 123, "status": "FILLED", "executedQty": "0.001", ...}

## 거래 내역 파싱

@staticmethod
parse_trade_history_response(api_response: list) -> TradeHistoryResponse
    Binance 체결 내역 응답 → TradeHistoryResponse.
    api_response = [{"id": 1, "price": "50000.0", "qty": "0.001", "time": 1234567890}, ...]
    각 항목을 SpotTrade 객체로 변환 후 TradeHistoryResponse로 래핑.

## 계정 정보 파싱

@staticmethod
parse_balance_response(api_response: dict) -> BalanceResponse
    Binance 계정 정보 응답 → BalanceResponse.
    api_response = {"balances": [{"asset": "BTC", "free": "1.0", "locked": "0.0"}, ...]}
    잔고 정보 추출 후 BalanceResponse로 래핑.

## 시장 데이터 파싱

@staticmethod
parse_ticker_response(api_response: dict) -> TickerResponse
    Binance 시세 응답 → TickerResponse.
    api_response = {"symbol": "BTCUSDT", "lastPrice": "50000.0", "volume": "1000.0", ...}

@staticmethod
parse_orderbook_response(api_response: dict) -> OrderbookResponse
    Binance 호가 응답 → OrderbookResponse.
    api_response = {"bids": [["50000.0", "1.0"], ...], "asks": [["50100.0", "1.0"], ...]}

@staticmethod
parse_candle_response(api_response: list) -> CandleResponse
    Binance K선 응답 → CandleResponse.
    api_response = [[openTime, open, high, low, close, volume, ...], ...]
    각 항목을 Candle 객체로 변환 후 CandleResponse로 래핑.

## 시스템 정보 파싱

@staticmethod
parse_market_list_response(api_response: dict) -> MarketListResponse
    Binance 거래소 정보 응답 → MarketListResponse.
    api_response = {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING", ...}, ...]}
    거래 가능한 심볼 목록 추출.

@staticmethod
parse_server_time_response(api_response: dict) -> ServerTimeResponse
    Binance 서버 시간 응답 → ServerTimeResponse.
    api_response = {"serverTime": 1234567890}
