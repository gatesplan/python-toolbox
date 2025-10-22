# spot-market-sell-worker Specification

## Purpose
TBD - created by archiving change implement-tradesim-simulation. Update Purpose after archive.
## Requirements
### Requirement: SpotMarketSellWorker MUST always execute

SpotMarketSellWorker MUST always execute market sell orders regardless of market price.

#### Scenario: Execute regardless of market price

**Given** 임의의 price 객체가 주어질 때
**When** `SpotMarketSellWorker()(order, price)`를 호출하면
**Then** 최소 1개 이상의 Trade를 반환해야 합니다

#### Scenario: Execute even with extreme prices

**Given** price.h가 10000이고 price.l이 5000일 때
**When** `SpotMarketSellWorker()(order, price)`를 호출하면
**Then** 최소 1개 이상의 Trade를 반환해야 합니다

### Requirement: SpotMarketSellWorker MUST apply slippage using tail range

SpotMarketSellWorker MUST apply slippage by executing at unfavorable prices in the candle tail range.

#### Scenario: Execution price is in tail range

**Given** price.l이 90이고 price.bodybottom()이 100일 때
**When** `SpotMarketSellWorker()(order, price)`를 호출하면
**Then** 각 Trade의 체결 가격은 90 이상 100 이하여야 합니다

#### Scenario: Slippage favors unfavorable price for seller

**Given** price의 tail 범위가 [90, 100]일 때
**When** 여러 번 호출하여 통계를 측정하면
**Then** 평균 체결 가격은 tail 범위의 중앙값보다 낮아야 합니다 (불리한 방향)

### Requirement: SpotMarketSellWorker MUST split into multiple trades

SpotMarketSellWorker MUST randomly split market sell orders into 1 to 3 Trade objects.

#### Scenario: Split into 1 to 3 trades

**Given** order.remaining_asset()이 10.0일 때
**When** `SpotMarketSellWorker()(order, price)`를 호출하면
**Then** 1~3개의 Trade를 반환해야 합니다
**And** 모든 Trade의 asset 합은 10.0이어야 합니다

#### Scenario: Each trade has different price

**Given** 2개 이상의 Trade가 생성될 때
**When** 각 Trade의 체결 가격을 확인하면
**Then** 대부분의 경우 각 Trade의 가격이 달라야 합니다 (tail 범위 내 재샘플링)

#### Scenario: Each trade has unique fill_id

**Given** 3개의 Trade가 생성될 때
**When** Trade 리스트를 확인하면
**Then** 각 Trade의 fill_id는 고유해야 합니다
**And** fill_id 형식은 "{order_id}-fill-{index}"여야 합니다

### Requirement: SpotMarketSellWorker MUST respect minimum trade amount

SpotMarketSellWorker MUST ensure each split Trade respects the minimum trade amount.

#### Scenario: Each split respects minimum amount

**Given** CalculationTool이 최소 거래 단위를 0.01로 설정했을 때
**When** Trade가 생성되면
**Then** 각 Trade의 asset 수량은 0.01의 배수여야 합니다

#### Scenario: Total amount is preserved after splitting

**Given** order.remaining_asset()이 7.77이고 최소 단위가 0.1일 때
**When** 3개로 분할하면
**Then** 모든 Trade asset의 합은 정확히 7.77이어야 합니다

### Requirement: SpotMarketSellWorker MUST create valid SpotTrade objects

SpotMarketSellWorker MUST create Trade objects that comply with the SpotTrade specification.

#### Scenario: Trade has correct stock address and side

**Given** order.stock_address가 StockAddress("binance", "BTCUSDT")일 때
**When** Trade가 생성되면
**Then** Trade.stock_address는 order.stock_address와 같아야 합니다
**And** Trade.side는 SpotSide.SELL이어야 합니다

#### Scenario: Trade has correct pair tokens

**Given** order.stock_address.base가 "BTC"이고 quote가 "USDT"일 때
**And** 체결 수량이 1.5 BTC이고 가격이 95 USDT일 때
**When** Trade가 생성되면
**Then** Trade.pair.asset.symbol은 "BTC"여야 합니다
**And** Trade.pair.asset.amount는 1.5여야 합니다
**And** Trade.pair.value.symbol은 "USDT"여야 합니다
**And** Trade.pair.value.amount는 142.5여야 합니다 (1.5 * 95)

#### Scenario: Trade has correct timestamp

**Given** price.t가 1640000000일 때
**When** Trade가 생성되면
**Then** Trade.timestamp는 1640000000이어야 합니다

