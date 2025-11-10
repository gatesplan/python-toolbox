# TradeSimulation
거래 시뮬레이션 API. 외부 진입점으로 여러 Service를 오케스트레이션하여 Order와 Price로부터 Trade 리스트를 생성한다.

`process(order: Order, price: Price) -> List[Trade]`
- raise ValueError: 알 수 없는 Order 타입, order_type, side
주문 체결 시뮬레이션을 실행한다. Order 타입과 Side에 따라 적절한 FillService를 선택하고, TradeFactoryService를 통해 Trade를 생성한다.
