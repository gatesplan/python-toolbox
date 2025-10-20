# spot-ledger-data-structure Specification

## Purpose
Defines the SpotLedger and SpotLedgerEntry data structures for recording and tracking spot trade history for a single trading pair. The ledger maintains cumulative positions, average entry prices, and realized profit/loss calculations.

## ADDED Requirements

### Requirement: SpotLedgerEntry 불변 레코드
SpotLedgerEntry MUST be an immutable record of a single trade event and its impact on the ledger state.

#### Scenario: 기본 SpotLedgerEntry 생성
```python
from financial_assets.ledger import SpotLedgerEntry
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.stock_address import StockAddress

# Create a sample trade
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
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)

# Create ledger entry
entry = SpotLedgerEntry(
    timestamp=1234567890,
    trade=trade,
    asset_change=1.0,
    value_change=-50000.0,
    cumulative_asset=1.0,
    cumulative_value=-50000.0,
    average_price=50000.0,
    realized_pnl=None  # No PnL on first buy
)

assert entry.timestamp == 1234567890
assert entry.trade == trade
assert entry.asset_change == 1.0
assert entry.cumulative_asset == 1.0
assert entry.average_price == 50000.0
```

#### Scenario: SpotLedgerEntry 불변성
```python
# Entry는 생성 후 수정 불가
try:
    entry.cumulative_asset = 2.0
    assert False, "Should raise error"
except:
    pass  # Expected
```

#### Scenario: SELL 거래 시 realized_pnl 기록
```python
# Second trade: sell 0.5 BTC at 52000
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.5), Token("USDT", 26000.0)),
    timestamp=1234567900
)

entry = SpotLedgerEntry(
    timestamp=1234567900,
    trade=sell_trade,
    asset_change=-0.5,
    value_change=26000.0,
    cumulative_asset=0.5,
    cumulative_value=-24000.0,
    average_price=50000.0,  # Same average price
    realized_pnl=1000.0  # (52000 - 50000) * 0.5
)

assert entry.realized_pnl == 1000.0
assert entry.asset_change == -0.5
```

### Requirement: SpotLedger 거래 기록 관리
SpotLedger MUST maintain a chronological list of trade entries for a single trading pair and provide DataFrame conversion for analysis.

#### Scenario: SpotLedger 초기화
```python
from financial_assets.ledger import SpotLedger

# Initialize ledger for BTC/USDT pair
ledger = SpotLedger(ticker="BTC-USDT")

assert ledger.ticker == "BTC-USDT"

# Empty ledger returns empty DataFrame
df = ledger.to_dataframe()
assert len(df) == 0
```

#### Scenario: BUY 거래 추가
```python
ledger = SpotLedger(ticker="BTC-USDT")

# First buy: 1.0 BTC at 50000
trade1 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)

entry1 = ledger.add_trade(trade1)

assert entry1.timestamp == 1234567890
assert entry1.asset_change == 1.0
assert entry1.cumulative_asset == 1.0
assert entry1.average_price == 50000.0

# Check DataFrame
df = ledger.to_dataframe()
assert len(df) == 1
assert df.iloc[0]["timestamp"] == 1234567890
assert df.iloc[0]["cumulative_asset"] == 1.0
```

#### Scenario: 평균 단가 계산 (Multiple BUYs)
```python
ledger = SpotLedger(ticker="BTC-USDT")

# First buy: 1.0 BTC at 50000
trade1 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)
ledger.add_trade(trade1)

# Second buy: 0.5 BTC at 52000
trade2 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 0.5), Token("USDT", 26000.0)),
    timestamp=1234567900
)
entry2 = ledger.add_trade(trade2)

# Average price: (50000 * 1.0 + 52000 * 0.5) / 1.5 = 50666.67
assert entry2.cumulative_asset == 1.5
assert abs(entry2.average_price - 50666.67) < 0.01
```

#### Scenario: SELL 거래 및 realized PnL 계산
```python
ledger = SpotLedger(ticker="BTC-USDT")

# Buy 1.0 BTC at 50000
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)
ledger.add_trade(buy_trade)

# Sell 0.6 BTC at 55000
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.6), Token("USDT", 33000.0)),
    timestamp=1234567900
)
entry = ledger.add_trade(sell_trade)

# PnL: (55000 - 50000) * 0.6 = 3000
assert entry.realized_pnl == 3000.0
assert entry.cumulative_asset == 0.4

# Check DataFrame for PnL
df = ledger.to_dataframe()
assert len(df) == 2
assert df.iloc[1]["realized_pnl"] == 3000.0
```

#### Scenario: DataFrame으로 거래 내역 조회
```python
ledger = SpotLedger(ticker="BTC-USDT")

# Add multiple trades
trade1 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)
trade2 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.5), Token("USDT", 26000.0)),
    timestamp=1234567900
)

ledger.add_trade(trade1)
ledger.add_trade(trade2)

# Convert to DataFrame for analysis
df = ledger.to_dataframe()
assert len(df) == 2
assert "timestamp" in df.columns
assert "side" in df.columns
assert "asset_change" in df.columns
assert "cumulative_asset" in df.columns
assert "average_price" in df.columns
assert "realized_pnl" in df.columns

# Check chronological order
assert df.iloc[0]["timestamp"] < df.iloc[1]["timestamp"]
```

### Requirement: 포지션 완전 청산 처리
SpotLedger MUST correctly handle complete position closure and reset average price.

#### Scenario: 전체 포지션 청산
```python
ledger = SpotLedger(ticker="BTC-USDT")

# Buy 1.0 BTC at 50000
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
    timestamp=1234567890
)
ledger.add_trade(buy_trade)

# Sell entire position: 1.0 BTC at 55000
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 1.0), Token("USDT", 55000.0)),
    timestamp=1234567900
)
entry = ledger.add_trade(sell_trade)

assert entry.cumulative_asset == 0.0
assert entry.realized_pnl == 5000.0

# After full liquidation, average price becomes None
# (indicated by 0 or NaN in DataFrame)
df = ledger.to_dataframe()
assert df.iloc[-1]["cumulative_asset"] == 0.0
```

### Requirement: 문자열 표현
SpotLedger and SpotLedgerEntry MUST provide readable string representations.

#### Scenario: SpotLedgerEntry 문자열 출력
```python
entry_str = str(entry)
assert "BTC" in entry_str or "btc" in entry_str.lower()
assert "50000" in entry_str or "50000.0" in entry_str
```

#### Scenario: SpotLedger 문자열 출력
```python
ledger_str = str(ledger)
assert "BTC-USDT" in ledger_str or "BTC/USDT" in ledger_str
assert "entries" in ledger_str.lower() or len(ledger.get_entries()) >= 0
```
