# OrderExecutor
주문 실행 및 체결 처리. TradeSimulation 위임 후 결과를 Portfolio에 반영하고 미체결 수량을 OrderBook에 등록.

_portfolio: Portfolio
_orderbook: OrderBook
_market_data: MarketData
_trade_simulation: TradeSimulation

execute_order(order: SpotOrder) -> list[Trade]
    raise ValueError
    주문 실행. MarketData에서 현재 Price 조회 후 TradeSimulation에 위임, 반환된 Trade들을 Portfolio에 반영. 미체결 수량이 있고 TimeInForce가 허용하면 OrderBook에 추가하고 자산 잠금. 체결된 Trade 리스트 반환.

cancel_order(order_id: str) -> None
    raise KeyError
    미체결 주문 취소. OrderBook에서 제거하고 잠긴 자산 해제.

---

**자산 잠금:**
- BUY: quote 화폐 잠금 (필요 금액 = 주문가격 * 미체결수량)
- SELL: base 화폐 잠금 (미체결수량)
- promise_id: order.order_id 사용

**TimeInForce 처리:**
- FOK: 완전 체결 아니면 실패 (Trade 비우고 예외 발생, OrderBook 추가 안 함)
- IOC: 부분 체결만 처리, 미체결 수량 즉시 취소 (OrderBook 추가 안 함)
- GTC/GTD: 미체결 수량 있으면 OrderBook 추가 및 자산 잠금

**실행 흐름:**
1. MarketData.get_current(symbol)로 현재 Price 조회
2. TradeSimulation.process(order, price) 호출
3. 반환된 Trade들을 순회하며 Portfolio.process_trade() 적용
4. 미체결 수량 = order.amount - sum(trade.amount)
5. TimeInForce 확인:
   - FOK: 미체결 있으면 Portfolio 롤백하고 예외 발생
   - IOC: 미체결 무시
   - GTC/GTD: OrderBook.add_order() + Portfolio.lock_currency()
6. 체결된 Trade 리스트 반환
