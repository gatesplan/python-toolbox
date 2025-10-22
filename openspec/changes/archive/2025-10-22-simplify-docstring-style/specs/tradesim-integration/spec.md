# Spec Delta: tradesim-integration

## MODIFIED Requirements

### Requirement: All tradesim module docstrings MUST be simplified to Korean

All classes and methods in the tradesim module SHALL use minimal Korean docstring style:
- Class docstrings MUST be 1-3 Korean lines describing responsibility
- Method docstrings MUST be single Korean line describing purpose only
- Args/Returns/Raises/Example sections MUST NOT be present
- Type hints SHALL remain unchanged

#### Scenario: TradeSimulation docstrings are concise Korean
**Given** the `TradeSimulation` class
**When** an agent reads the class docstring
**Then** the docstring is 2-3 Korean lines: "거래 시뮬레이션 코어 클래스. Order의 타입(limit/market)과 side(buy/sell)를 검사하여 적절한 워커로 라우팅합니다."
**And** no method list or Args/Returns sections are present

**Given** `process` method in `TradeSimulation`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "Order를 처리하여 Trade 리스트 반환."

**Given** `_validate_process_param` method in `TradeSimulation`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "파라미터 타입 검증."

#### Scenario: TradeFactory docstrings are simplified Korean
**Given** the `TradeFactory` class
**When** an agent reads the class docstring
**Then** the docstring is 2-3 Korean lines describing Trade creation responsibility
**And** no method list is present

**Given** `create_spot_trade` method in `TradeFactory`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "단일 SpotTrade 생성 (수수료 자동 계산)."

**Given** `create_spot_trades_from_amounts` method in `TradeFactory`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "분할 수량으로 여러 Trade 생성 (각각 수수료 계산)."

**Given** `create_market_trades_with_slippage` method in `TradeFactory`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "시장가 주문용 - 각 Trade마다 다른 가격 및 수수료 계산."

#### Scenario: Worker docstrings are simplified Korean
**Given** `SpotLimitWorker` class
**When** an agent reads the class docstring
**Then** the docstring is 1-2 Korean lines: "지정가 주문 워커 (BUY/SELL 통합). 매수: 시장 가격이 주문 가격 이하일 때 체결, 매도: 시장 가격이 주문 가격 이상일 때 체결."
**And** `__call__` method has 1 Korean line: "지정가 주문 체결."

**Given** `SpotMarketBuyWorker` class
**When** an agent reads the class docstring
**Then** the docstring is 1-2 Korean lines: "시장가 매수 주문 워커. 항상 체결되며 슬리피지를 반영합니다 (head 범위 내 불리한 가격)."
**And** `__call__` method has 1 Korean line: "시장가 매수 체결."

**Given** `SpotMarketSellWorker` class
**When** an agent reads the class docstring
**Then** the docstring is 1-2 Korean lines: "시장가 매도 주문 워커. 항상 체결되며 슬리피지를 반영합니다 (tail 범위 내 불리한 가격)."
**And** `__call__` method has 1 Korean line: "시장가 매도 체결."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in all tradesim modules
**When** running `pytest packages/financial-simulation/tests/`
**Then** all 28 tests pass
**And** no functional behavior has changed

## Related Changes
- `calculation-tool`: Docstring simplification pattern
