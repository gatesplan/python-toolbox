# Spec: SpotLimitSellWorker

## Overview

지정가 매도 주문의 체결을 시뮬레이션하는 워커입니다. 매수와 반대로 시장 가격이 주문 가격 이상일 때 체결됩니다.

## ADDED Requirements

### Requirement: SpotLimitSellWorker MUST execute when market price is above or equal to order price

SpotLimitSellWorker MUST execute limit sell orders when the market price is above or equal to the order price.

#### Scenario: Execute when market price equals order price

**Given** order.price가 100이고 price.c가 100일 때
**When** `SpotLimitSellWorker()(order, price)`를 호출하면
**Then** 최소 1개 이상의 Trade를 반환해야 합니다

#### Scenario: Execute when market price is above order price

**Given** order.price가 100이고 price.c가 105일 때
**When** `SpotLimitSellWorker()(order, price)`를 호출하면
**Then** 최소 1개 이상의 Trade를 반환해야 합니다

#### Scenario: Not execute when market price is below order price

**Given** order.price가 100이고 price.c가 95일 때
**When** `SpotLimitSellWorker()(order, price)`를 호출하면
**Then** 빈 리스트를 반환해야 합니다

### Requirement: SpotLimitSellWorker MUST fully execute in body range

SpotLimitSellWorker MUST fully execute orders when the order price is within the candle body range.

#### Scenario: Full execution in body range

**Given** price.bodybottom()이 98이고 price.bodytop()이 102일 때
**And** order.price가 100 (body 범위 내)일 때
**When** `SpotLimitSellWorker()(order, price)`를 호출하면
**Then** 정확히 1개의 Trade를 반환해야 합니다
**And** Trade.pair.asset.amount는 order.remaining_asset()과 같아야 합니다
**And** 체결 가격은 order.price여야 합니다

#### Scenario: Execution price is order price in body range

**Given** order.price가 100이고 가격이 body 범위 내에 있을 때
**When** 체결이 발생하면
**Then** Trade.pair.value.amount / Trade.pair.asset.amount는 100이어야 합니다

### Requirement: SpotLimitSellWorker MUST probabilistically execute in head/tail range

SpotLimitSellWorker MUST probabilistically execute orders when the order price is in the candle head or tail range.

#### Scenario: Probabilistic execution in head range

**Given** price.bodytop()이 102이고 price.h가 110일 때
**And** order.price가 105 (head 범위)일 때
**When** `SpotLimitSellWorker()(order, price)`를 100번 호출하면
**Then** 약 70번 정도는 체결이 발생해야 합니다 (30% 실패, 70% 성공)

#### Scenario: Probabilistic execution in tail range

**Given** price.l이 90이고 price.bodybottom()이 98일 때
**And** order.price가 95 (tail 범위)일 때
**When** `SpotLimitSellWorker()(order, price)`를 100번 호출하면
**Then** 약 70번 정도는 체결이 발생해야 합니다

### Requirement: SpotLimitSellWorker MUST support partial fills

SpotLimitSellWorker MUST split partial fills into multiple Trade objects.

#### Scenario: Partial fill splits into multiple trades

**Given** 부분 체결이 발생할 때
**When** `SpotLimitSellWorker()(order, price)`를 호출하면
**Then** 1~3개의 Trade를 반환해야 합니다
**And** 모든 Trade의 asset 합은 order.remaining_asset() 이하여야 합니다

#### Scenario: Each partial fill has unique fill_id

**Given** 부분 체결로 2개의 Trade가 생성될 때
**When** Trade 리스트를 확인하면
**Then** 각 Trade의 fill_id는 고유해야 합니다

#### Scenario: Partial fill respects minimum trade amount

**Given** CalculationTool을 사용하여 수량을 분할할 때
**When** 부분 체결이 발생하면
**Then** 각 Trade의 수량은 최소 거래 단위의 배수여야 합니다

### Requirement: SpotLimitSellWorker MUST create valid SpotTrade objects

SpotLimitSellWorker MUST create Trade objects that comply with the SpotTrade specification.

#### Scenario: Trade has correct stock address and side

**Given** order.stock_address가 StockAddress("binance", "BTCUSDT")일 때
**When** Trade가 생성되면
**Then** Trade.stock_address는 order.stock_address와 같아야 합니다
**And** Trade.side는 SpotSide.SELL이어야 합니다

#### Scenario: Trade has correct pair tokens

**Given** order.stock_address.base가 "BTC"이고 quote가 "USDT"일 때
**And** 체결 수량이 1.5 BTC이고 가격이 100 USDT일 때
**When** Trade가 생성되면
**Then** Trade.pair.asset.symbol은 "BTC"여야 합니다
**And** Trade.pair.asset.amount는 1.5여야 합니다
**And** Trade.pair.value.symbol은 "USDT"여야 합니다
**And** Trade.pair.value.amount는 150여야 합니다

#### Scenario: Trade has correct timestamp

**Given** price.t가 1640000000일 때
**When** Trade가 생성되면
**Then** Trade.timestamp는 1640000000이어야 합니다
