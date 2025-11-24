# SpotExchange
Spot 거래소 API Layer. 외부 시스템의 진입점으로 주문 생성, 취소, 잔고 조회, 시장 틱 처리 등 전체 거래소 기능을 제공.

_portfolio: Portfolio
_orderbook: OrderBook
_order_history: OrderHistory
_market_data: MarketData
_order_validator: OrderValidator
_order_executor: OrderExecutor
_position_manager: PositionManager
_trade_history: list[SpotTrade]    # 전체 체결 내역
_initial_balance: float            # 초기 자산
_quote_currency: str               # 기준 화폐

## 초기화

__init__(initial_balance: float, market_data: MarketData, trade_simulation: TradeSimulation, quote_currency: str = "USDT") -> None
    SpotExchange 초기화. Portfolio에 초기 자금 입금하고 모든 Service/Core 컴포넌트 생성.

    Args:
        initial_balance: 초기 자산 (quote_currency 기준)
        market_data: MarketData 인스턴스 (외부에서 데이터 로드 후 전달)
        trade_simulation: TradeSimulation 인스턴스 (체결 시뮬레이션)
        quote_currency: 기준 화폐 (기본값: "USDT")

## 주문 관리

place_order(order: SpotOrder) -> list[SpotTrade]
    raise ValueError
    주문 실행. OrderValidator로 검증 후 OrderExecutor로 실행. 체결 내역을 trade_history에 추가하고 반환.

    Args:
        order: 완성된 SpotOrder 객체 (financial-gateway에서 생성하여 전달)

    Returns:
        list[SpotTrade]: 체결된 Trade 리스트 (미체결은 OrderBook에 등록)

cancel_order(order_id: str) -> None
    raise KeyError
    미체결 주문 취소. OrderExecutor.cancel_order() 위임.

get_order(order_id: str) -> SpotOrder | None
    개별 주문 조회 (미체결 + 이력). OrderBook과 OrderHistory에서 조회.

    Args:
        order_id: 주문 ID

    Returns:
        SpotOrder | None: 주문 객체 또는 None (미체결 우선, 없으면 이력에서 조회)

get_order_status(order_id: str) -> OrderStatus | None
    주문 상태 조회. OrderHistory에서 최신 상태 반환.

    Args:
        order_id: 주문 ID

    Returns:
        OrderStatus | None: 주문 상태 (NEW, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED, REJECTED) 또는 None

get_open_orders(symbol: str | None = None) -> list[SpotOrder]
    미체결 주문 조회. symbol 지정 시 해당 심볼만 반환, 미지정 시 전체 반환.

get_trade_history(symbol: str | None = None) -> list[SpotTrade]
    체결 내역 조회. symbol 지정 시 해당 심볼만 필터링.

    Args:
        symbol: 필터링할 심볼 (예: "BTC/USDT"). None이면 전체 반환

## 잔고 및 포지션 조회

get_balance(currency: str | None = None) -> float | dict[str, float]
    Currency 잔고 조회 (Portfolio.get_available_balance() 래핑)

    Args:
        currency: 화폐 심볼 (예: "USDT"). None이면 전체 잔고 반환

    Returns:
        float | dict[str, float]: 단일 화폐는 float, 전체 조회는 {symbol: balance}

get_positions() -> dict[str, float]
    보유 포지션 조회 (PositionManager.get_positions() 래핑)

    Returns:
        dict[str, float]: {ticker: amount} 형식 (예: {"BTC-USDT": 0.5})

get_position_value(ticker: str) -> dict[str, float]
    특정 포지션의 상세 가치 정보

    Returns:
        dict: {
            "book_value": float,      # 매수 당시 가치
            "market_value": float,    # 현재 시장 가치
            "pnl": float,             # 손익 (절대값)
            "pnl_ratio": float        # 손익률 (%)
        }

get_total_value() -> float
    총 자산 가치 (PositionManager.get_total_value() 래핑)

get_statistics() -> dict[str, float]
    포트폴리오 통계 조회

    Returns:
        dict: {
            "total_value": float,          # 총 자산 가치
            "total_pnl": float,            # 총 손익
            "total_pnl_ratio": float,      # 총 손익률 (%)
            "currency_value": float,       # Currency 가치
            "position_value": float,       # Position 총 가치
            "allocation": dict[str, float] # 자산 배분 비중 (%)
        }

## 시장 틱 관리

step() -> bool
    다음 시장 틱으로 이동. MarketData.step() 호출 후 OrderBook의 만료 주문 처리.

    Returns:
        bool: True면 계속 진행 가능, False면 시뮬레이션 종료

reset() -> None
    거래소 초기화. Portfolio 리셋, OrderBook 클리어, MarketData 커서 리셋, trade_history 초기화.

get_current_timestamp() -> int | None
    현재 시장 타임스탬프 조회 (MarketData.get_current_timestamp() 래핑)

get_current_price(symbol: str) -> float | None
    현재 시장 가격 조회 (MarketData.get_current(symbol).close)

is_finished() -> bool
    시뮬레이션 종료 여부 (MarketData.is_finished() 래핑)

---

**주문 생성 흐름:**
1. place_order(order) 호출 (order는 gateway에서 이미 생성됨)
2. OrderValidator.validate_order(order) (거래소 컨텍스트 검증)
3. OrderExecutor.execute_order(order) (체결 처리)
4. 반환된 SpotTrade들을 _trade_history에 추가
5. SpotTrade 리스트 반환

**책임 분리:**
- **financial-gateway**: 사용자 의도 → SpotOrder 객체 생성 (order_id, timestamp, StockAddress 등)
- **SpotExchange**: 완성된 Order 수신 → 검증 → 실행 → 이력 관리

**시장 틱 처리 흐름:**
1. step() 호출
2. MarketData.step() (커서 이동)
3. current_timestamp = MarketData.get_current_timestamp()
4. OrderBook.expire_orders(current_timestamp) (GTD 만료 처리)
5. 만료된 주문들의 자산 잠금 해제 (Portfolio.unlock_currency())
6. 시뮬레이션 종료 여부 반환

**초기화 과정:**
```python
# MarketData, TradeSimulation 생성
market_data = MarketData(data=loaded_data)
trade_simulation = TradeSimulation()

# SpotExchange 초기화
exchange = SpotExchange(
    initial_balance=100000.0,
    market_data=market_data,
    trade_simulation=trade_simulation,
    quote_currency="USDT"
)

# 내부적으로:
# 1. Portfolio 생성 및 초기 자금 입금 (quote_currency 기준)
# 2. OrderBook 생성
# 3. OrderValidator(portfolio, market_data) 생성
# 4. OrderExecutor(portfolio, orderbook, market_data, trade_simulation) 생성
# 5. PositionManager(portfolio, market_data, initial_balance) 생성
```

**사용 예시:**
```python
# gateway에서 Order 생성 (예시)
order = SpotOrder(
    order_id="order_001",
    stock_address=StockAddress("BTC", "USDT"),
    side=Side.BUY,
    order_type=OrderType.LIMIT,
    price=45000.0,
    amount=0.5,
    timestamp=exchange.get_current_timestamp(),
    time_in_force=TimeInForce.GTC
)

# Exchange에 주문 전달
trades = exchange.place_order(order)

# 잔고 조회
usdt_balance = exchange.get_balance("USDT")  # 50000.0
all_balances = exchange.get_balance()        # {"USDT": 50000.0, ...}

# 포지션 조회
positions = exchange.get_positions()         # {"BTC-USDT": 0.5}
btc_value = exchange.get_position_value("BTC-USDT")
# {"book_value": 22500, "market_value": 25000, "pnl": 2500, "pnl_ratio": 11.11}

# 통계 조회
stats = exchange.get_statistics()
# {"total_value": 102500, "total_pnl": 2500, "total_pnl_ratio": 2.5, ...}

# 시장 틱 진행
while not exchange.is_finished():
    # 트레이딩 로직
    current_price = exchange.get_current_price("BTC/USDT")

    # 시장 진행
    exchange.step()

# 주문 취소
exchange.cancel_order("order_123")
```

**의존성:**
- Portfolio: 잔고 및 자산 관리
- OrderBook: 미체결 주문 관리
- MarketData: 시장 데이터 및 시간 관리
- OrderValidator: 주문 검증
- OrderExecutor: 주문 실행
- PositionManager: 포지션 통계
- TradeSimulation: 체결 시뮬레이션 (외부 tradesim 모듈)

**외부 연동:**
- financial-gateway가 이 API를 통해 거래소와 통신
- StockAddress는 financial-assets 패키지의 심볼 표현 객체
- Order, Trade, Price 등도 financial-assets에서 제공

**설계 원칙:**
- API Layer는 완성된 도메인 객체(SpotOrder)를 받아 처리
- 객체 생성 및 변환은 gateway 책임 (관심사 분리)
- 모든 비즈니스 로직은 Service/Core Layer에 위임
- 상태 변경 이력 추적 (trade_history)
- financial-assets 패키지의 도메인 객체 완전 활용
