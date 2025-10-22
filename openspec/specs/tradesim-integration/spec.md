# tradesim-integration Specification

## Purpose
TBD - created by archiving change implement-tradesim-simulation. Update Purpose after archive.
## Requirements
### Requirement: TradeSimulation MUST initialize with CalculationTool

TradeSimulation MUST create and hold a CalculationTool instance upon initialization.

#### Scenario: Initialize with CalculationTool

**Given** TradeSimulation을 초기화할 때
**When** `TradeSimulation()`을 호출하면
**Then** 내부적으로 CalculationTool 인스턴스를 생성해야 합니다
**And** 워커들이 이 인스턴스에 접근할 수 있어야 합니다

#### Scenario: CalculationTool is accessible to workers

**Given** TradeSimulation 인스턴스가 생성되었을 때
**When** 워커가 호출되면
**Then** 워커는 TradeSimulation의 calc_tool에 접근할 수 있어야 합니다

### Requirement: TradeSimulation MUST pass itself to workers

TradeSimulation MUST pass itself as the first parameter when calling workers.

#### Scenario: Pass simulation instance to limit buy worker

**Given** TradeSimulation 인스턴스 sim이 있을 때
**When** limit buy 주문을 처리하면
**Then** `_limit_buy_worker(sim, order, price)`가 호출되어야 합니다

#### Scenario: Pass simulation instance to market sell worker

**Given** TradeSimulation 인스턴스 sim이 있을 때
**When** market sell 주문을 처리하면
**Then** `_market_sell_worker(sim, order, price)`가 호출되어야 합니다

### Requirement: TradeSimulation MUST maintain existing routing logic

TradeSimulation MUST maintain the existing routing logic for order type and side.

#### Scenario: Route limit buy orders correctly

**Given** order.order_type이 "limit"이고 side가 SpotSide.BUY일 때
**When** `process(order, price)`를 호출하면
**Then** SpotLimitBuyWorker가 호출되어야 합니다

#### Scenario: Route market sell orders correctly

**Given** order.order_type이 "market"이고 side가 SpotSide.SELL일 때
**When** `process(order, price)`를 호출하면
**Then** SpotMarketSellWorker가 호출되어야 합니다

#### Scenario: Validate parameters before routing

**Given** 잘못된 order 또는 price가 주어질 때
**When** `process(order, price)`를 호출하면
**Then** ValueError를 발생시켜야 합니다

### Requirement: Workers MUST access CalculationTool through TradeSimulation

All workers MUST access CalculationTool through the TradeSimulation instance.

#### Scenario: Worker accesses calc_tool for rounding

**Given** 워커가 최소 거래 단위로 반올림해야 할 때
**When** 워커 내부에서 계산을 수행하면
**Then** `sim.calc_tool.round_to_min_amount()`를 호출해야 합니다

#### Scenario: Worker accesses calc_tool for price sampling

**Given** 워커가 가격 샘플링이 필요할 때
**When** 워커 내부에서 계산을 수행하면
**Then** `sim.calc_tool.get_price_sample()`을 호출해야 합니다

#### Scenario: Worker accesses calc_tool for amount separation

**Given** 워커가 수량 분할이 필요할 때
**When** 워커 내부에서 계산을 수행하면
**Then** `sim.calc_tool.get_separated_amount_sequence()`를 호출해야 합니다

### Requirement: TradeSimulation MUST expose calc_tool as public attribute

TradeSimulation MUST expose calc_tool as a public attribute for testing and extensibility.

#### Scenario: Access calc_tool from outside

**Given** TradeSimulation 인스턴스 sim이 있을 때
**When** `sim.calc_tool`에 접근하면
**Then** CalculationTool 인스턴스를 반환해야 합니다

#### Scenario: Replace calc_tool for testing

**Given** 테스트 환경에서 mock calc_tool을 사용하고 싶을 때
**When** `sim.calc_tool = mock_calc_tool`을 설정하면
**Then** 워커들이 mock_calc_tool을 사용해야 합니다

