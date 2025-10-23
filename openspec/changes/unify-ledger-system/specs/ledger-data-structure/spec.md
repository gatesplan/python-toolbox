## ADDED Requirements

### Requirement: LedgerEntry 불변 레코드
LedgerEntry MUST be an immutable record of any wallet operation (deposit, withdraw, trade, fee) with signed changes and cumulative balances.

#### Scenario: 화폐 입금 기록
```python
from financial_assets.ledger import LedgerEntry, EventType

# 화폐 입금: asset_change=0, value_change=+10000
entry = LedgerEntry(
    timestamp=1234567890,
    account="USDT",
    event=EventType.DEPOSIT,
    asset_change=0.0,
    value_change=10000.0,
    asset=0.0,
    value=10000.0
)

assert entry.timestamp == 1234567890
assert entry.account == "USDT"
assert entry.event == EventType.DEPOSIT
assert entry.asset_change == 0.0
assert entry.value_change == 10000.0
assert entry.asset == 0.0
assert entry.value == 10000.0
```

#### Scenario: BUY 거래 기록
```python
# BTC-USDT BUY: asset +0.001, value -100
entry = LedgerEntry(
    timestamp=1234567900,
    account="BTC-USDT",
    event=EventType.BUY,
    asset_change=0.001,
    value_change=-100.0,
    asset=0.001,
    value=-100.0
)

assert entry.event == EventType.BUY
assert entry.asset_change > 0
assert entry.value_change < 0
```

#### Scenario: 수수료 기록
```python
# 수수료: asset_change=0, value_change=-0.1
entry = LedgerEntry(
    timestamp=1234567901,
    account="BTC-USDT",
    event=EventType.FEE,
    asset_change=0.0,
    value_change=-0.1,
    asset=0.001,
    value=-100.1
)

assert entry.event == EventType.FEE
assert entry.asset_change == 0.0
assert entry.value_change < 0
```

#### Scenario: LedgerEntry 불변성
```python
# Entry는 생성 후 수정 불가
try:
    entry.asset = 2.0
    assert False, "Should raise error"
except:
    pass  # Expected: frozen dataclass
```

### Requirement: EventType 열거형
EventType MUST define all wallet operation types: DEPOSIT, WITHDRAW, BUY, SELL, FEE.

#### Scenario: EventType 값 확인
```python
from financial_assets.ledger import EventType

assert EventType.DEPOSIT.value == "deposit"
assert EventType.WITHDRAW.value == "withdraw"
assert EventType.BUY.value == "buy"
assert EventType.SELL.value == "sell"
assert EventType.FEE.value == "fee"
```

### Requirement: Ledger 계정별 작업 기록
Ledger MUST maintain a chronological list of all operations for a single account (currency or ticker) with cumulative tracking.

#### Scenario: Ledger 초기화
```python
from financial_assets.ledger import Ledger

# 화폐 계정 ledger
ledger = Ledger(account="USDT")
assert ledger.account == "USDT"
assert len(ledger.get_entries()) == 0

# 자산 계정 ledger
ticker_ledger = Ledger(account="BTC-USDT")
assert ticker_ledger.account == "BTC-USDT"
```

#### Scenario: 화폐 입금 기록
```python
ledger = Ledger(account="USDT")

entry = ledger.add_currency_deposit(timestamp=100, amount=10000.0)

assert entry.event == EventType.DEPOSIT
assert entry.asset_change == 0.0
assert entry.value_change == 10000.0
assert entry.asset == 0.0
assert entry.value == 10000.0

# Ledger에 기록됨
entries = ledger.get_entries()
assert len(entries) == 1
assert entries[0] == entry
```

#### Scenario: 화폐 출금 기록
```python
ledger = Ledger(account="USDT")
ledger.add_currency_deposit(timestamp=100, amount=10000.0)

entry = ledger.add_currency_withdraw(timestamp=200, amount=3000.0)

assert entry.event == EventType.WITHDRAW
assert entry.asset_change == 0.0
assert entry.value_change == -3000.0
assert entry.asset == 0.0
assert entry.value == 7000.0  # 10000 - 3000
```

#### Scenario: 자산 입금 기록
```python
ledger = Ledger(account="BTC-USDT")

entry = ledger.add_asset_deposit(timestamp=100, amount=0.5)

assert entry.event == EventType.DEPOSIT
assert entry.asset_change == 0.5
assert entry.value_change == 0.0
assert entry.asset == 0.5
assert entry.value == 0.0
```

#### Scenario: 자산 출금 기록
```python
ledger = Ledger(account="BTC-USDT")
ledger.add_asset_deposit(timestamp=100, amount=1.0)

entry = ledger.add_asset_withdraw(timestamp=200, amount=0.3)

assert entry.event == EventType.WITHDRAW
assert entry.asset_change == -0.3
assert entry.value_change == 0.0
assert entry.asset == 0.7  # 1.0 - 0.3
assert entry.value == 0.0
```

#### Scenario: 거래 기록 (BUY)
```python
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress

ledger = Ledger(account="BTC-USDT")

stock_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="spot",
    base="btc",
    quote="usdt",
    timeframe="1d"
)

trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 0.001), Token("USDT", 100.0)),
    timestamp=100
)

entry = ledger.add_trade(trade)

assert entry.event == EventType.BUY
assert entry.asset_change == 0.001
assert entry.value_change == -100.0
assert entry.asset == 0.001
assert entry.value == -100.0
```

#### Scenario: 거래 기록 (SELL)
```python
ledger = Ledger(account="BTC-USDT")

# First BUY
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 0.001), Token("USDT", 100.0)),
    timestamp=100
)
ledger.add_trade(buy_trade)

# Then SELL
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.0006), Token("USDT", 66.0)),
    timestamp=200
)
entry = ledger.add_trade(sell_trade)

assert entry.event == EventType.SELL
assert entry.asset_change == -0.0006
assert entry.value_change == 66.0
assert entry.asset == 0.0004  # 0.001 - 0.0006
assert entry.value == -34.0  # -100 + 66
```

#### Scenario: 수수료 기록
```python
ledger = Ledger(account="BTC-USDT")
ledger.add_currency_deposit(timestamp=100, amount=1000.0)

entry = ledger.add_fee(timestamp=200, amount=0.5)

assert entry.event == EventType.FEE
assert entry.asset_change == 0.0
assert entry.value_change == -0.5
assert entry.asset == 0.0
assert entry.value == 999.5
```

### Requirement: DataFrame 변환
Ledger MUST provide DataFrame conversion for analysis with all entry fields.

#### Scenario: 빈 ledger의 DataFrame
```python
ledger = Ledger(account="USDT")

df = ledger.to_dataframe()

assert len(df) == 0
assert "timestamp" in df.columns
assert "account" in df.columns
assert "event" in df.columns
assert "asset_change" in df.columns
assert "value_change" in df.columns
assert "asset" in df.columns
assert "value" in df.columns
```

#### Scenario: 여러 작업 후 DataFrame 생성
```python
ledger = Ledger(account="USDT")

ledger.add_currency_deposit(timestamp=100, amount=10000.0)
ledger.add_currency_withdraw(timestamp=200, amount=2000.0)
ledger.add_fee(timestamp=300, amount=10.0)

df = ledger.to_dataframe()

assert len(df) == 3
assert df.iloc[0]["event"] == "deposit"
assert df.iloc[0]["value_change"] == 10000.0
assert df.iloc[1]["event"] == "withdraw"
assert df.iloc[1]["value_change"] == -2000.0
assert df.iloc[2]["event"] == "fee"
assert df.iloc[2]["value_change"] == -10.0

# 시간순 정렬 확인
assert df.iloc[0]["timestamp"] < df.iloc[1]["timestamp"]
assert df.iloc[1]["timestamp"] < df.iloc[2]["timestamp"]
```

### Requirement: 누적 추적 정확성
Ledger MUST accurately track cumulative asset and value across all operations.

#### Scenario: 복합 작업 후 누적 추적
```python
ledger = Ledger(account="BTC-USDT")

# Asset deposit
ledger.add_asset_deposit(timestamp=100, amount=1.0)
# Value deposit
ledger.add_currency_deposit(timestamp=200, amount=50000.0)
# Asset withdraw
ledger.add_asset_withdraw(timestamp=300, amount=0.3)
# Fee
ledger.add_fee(timestamp=400, amount=100.0)

entries = ledger.get_entries()

# 최종 누적값 확인
assert entries[-1].asset == 0.7  # 1.0 - 0.3
assert entries[-1].value == 49900.0  # 50000 - 100
```

### Requirement: 문자열 표현
Ledger and LedgerEntry MUST provide readable string representations.

#### Scenario: LedgerEntry 문자열 출력
```python
entry = LedgerEntry(
    timestamp=100,
    account="USDT",
    event=EventType.DEPOSIT,
    asset_change=0.0,
    value_change=10000.0,
    asset=0.0,
    value=10000.0
)

entry_str = str(entry)
assert "USDT" in entry_str or "usdt" in entry_str.lower()
assert "DEPOSIT" in entry_str or "deposit" in entry_str.lower()
```

#### Scenario: Ledger 문자열 출력
```python
ledger = Ledger(account="BTC-USDT")
ledger.add_currency_deposit(timestamp=100, amount=1000.0)

ledger_str = str(ledger)
assert "BTC-USDT" in ledger_str
assert "entries" in ledger_str.lower() or "1" in ledger_str
```
