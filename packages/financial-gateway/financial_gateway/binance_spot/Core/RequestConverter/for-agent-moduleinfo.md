# RequestConverter

Request 객체를 Binance API 파라미터(dict)로 변환하는 순수 변환 로직. 모든 메서드는 정적 메서드로 Stateless하게 동작한다.

## 주문 요청 변환

@staticmethod
convert_limit_buy(request: LimitBuyOrderRequest) -> dict
    지정가 매수 Request → Binance API params.
    return {"symbol": request.address, "side": "BUY", "type": "LIMIT", "timeInForce": "GTC", "price": request.price, "quantity": request.volume}

@staticmethod
convert_limit_sell(request: LimitSellOrderRequest) -> dict
    지정가 매도 Request → Binance API params.
    return {"symbol": request.address, "side": "SELL", "type": "LIMIT", "timeInForce": "GTC", "price": request.price, "quantity": request.volume}

@staticmethod
convert_market_buy(request: MarketBuyOrderRequest) -> dict
    시장가 매수 Request → Binance API params.
    return {"symbol": request.address, "side": "BUY", "type": "MARKET", "quantity": request.volume}

@staticmethod
convert_market_sell(request: MarketSellOrderRequest) -> dict
    시장가 매도 Request → Binance API params.
    return {"symbol": request.address, "side": "SELL", "type": "MARKET", "quantity": request.volume}

## 주문 관리 변환

@staticmethod
convert_cancel_order(request: CancelOrderRequest) -> dict
    주문 취소 Request → Binance API params.
    return {"symbol": request.address, "orderId": request.order_id}

@staticmethod
convert_order_status_query(request: OrderStatusRequest) -> dict
    주문 상태 조회 Request → Binance API params.
    return {"symbol": request.address, "orderId": request.order_id}

@staticmethod
convert_trade_history_query(request: TradeHistoryRequest) -> dict
    체결 내역 조회 Request → Binance API params.
    return {"symbol": request.address, "limit": request.limit or 500}

## 시장 데이터 변환

@staticmethod
convert_ticker_query(request: TickerRequest) -> dict
    시세 조회 Request → Binance API params.
    return {"symbol": request.address}

@staticmethod
convert_orderbook_query(request: OrderbookRequest) -> dict
    호가 조회 Request → Binance API params.
    return {"symbol": request.address, "limit": request.depth or 100}

@staticmethod
convert_candle_query(request: CandleRequest) -> dict
    캔들 조회 Request → Binance API params.
    interval_map = {"1m": "1m", "5m": "5m", "1h": "1h", "1d": "1d"}
    return {"symbol": request.address, "interval": interval_map[request.timeframe], "limit": request.limit or 500}
