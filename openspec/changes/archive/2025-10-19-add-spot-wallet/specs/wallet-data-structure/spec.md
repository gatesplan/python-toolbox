# wallet-data-structure Specification

## Purpose
현물 거래 계정의 자산 및 거래 내역을 관리하는 SpotWallet 데이터 구조를 정의합니다. SpotWallet은 화폐 계정 관리, PairStack을 통한 자산 포지션 관리, SpotLedger를 통한 거래 기록을 담당합니다.

## ADDED Requirements

### Requirement: SpotWallet 초기화 및 화폐 관리
SpotWallet MUST manage currency balances (quote currencies like USD, KRW) through deposit and withdrawal operations.

#### Scenario: SpotWallet 초기화
```python
from financial_assets.wallet import SpotWallet

# 빈 지갑 생성
wallet = SpotWallet()

# 초기 상태: 화폐 목록 및 티커 목록 비어있음
assert wallet.list_currencies() == []
assert wallet.list_tickers() == []
```

#### Scenario: 화폐 입금
```python
wallet = SpotWallet()

# USD 입금
wallet.deposit_currency(symbol="USD", amount=10000.0)

# 잔액 확인
assert wallet.get_currency_balance("USD") == 10000.0
assert "USD" in wallet.list_currencies()
```

#### Scenario: 화폐 출금
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=10000.0)

# USD 출금
wallet.withdraw_currency(symbol="USD", amount=3000.0)

# 잔액 확인
assert wallet.get_currency_balance("USD") == 7000.0
```

#### Scenario: 잔액 부족 시 출금 실패
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=1000.0)

# 잔액 초과 출금 시도
try:
    wallet.withdraw_currency(symbol="USD", amount=2000.0)
    assert False, "Should raise error"
except ValueError as e:
    assert "insufficient balance" in str(e).lower()
```

#### Scenario: 없는 화폐 조회
```python
wallet = SpotWallet()

# 입금하지 않은 화폐 조회
assert wallet.get_currency_balance("BTC") == 0.0
```

### Requirement: BUY 거래 처리
SpotWallet MUST process BUY trades by deducting quote currency and adding to PairStack.

#### Scenario: BUY 거래 처리
```python
from financial_assets.wallet import SpotWallet
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

stock_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="spot",
    base="btc",
    quote="usd",
    timeframe="1d"
)

# BUY: 1.0 BTC at 50000 USD
trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)

wallet.process_trade(trade)

# USD 잔액 확인 (100000 - 50000 = 50000)
assert wallet.get_currency_balance("USD") == 50000.0

# PairStack 확인
pair_stack = wallet.get_pair_stack("BTC-USD")
assert pair_stack is not None
assert pair_stack.total_asset_amount() == 1.0
assert pair_stack.total_value_amount() == 50000.0
assert pair_stack.mean_value() == 50000.0

# Ledger 확인
ledger = wallet.get_ledger("BTC-USD")
assert ledger is not None
df = ledger.to_dataframe()
assert len(df) == 1
assert df.iloc[0]["side"] == "buy"
```

#### Scenario: 잔액 부족으로 BUY 실패
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=1000.0)

trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567900
)

try:
    wallet.process_trade(trade)
    assert False, "Should raise error"
except ValueError as e:
    assert "insufficient balance" in str(e).lower()
```

#### Scenario: 여러 번 BUY - PairStack 레이어 관리
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=200000.0)

# First buy: 1.0 BTC at 50000
trade1 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(trade1)

# Second buy: 0.5 BTC at 52000 (평단가 차이로 새 레이어)
trade2 = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
    timestamp=1234567900
)
wallet.process_trade(trade2)

# PairStack 확인
pair_stack = wallet.get_pair_stack("BTC-USD")
assert pair_stack.total_asset_amount() == 1.5
assert pair_stack.total_value_amount() == 76000.0
# 평단가: 76000 / 1.5 = 50666.67
assert abs(pair_stack.mean_value() - 50666.67) < 0.01

# USD 잔액: 200000 - 50000 - 26000 = 124000
assert wallet.get_currency_balance("USD") == 124000.0
```

### Requirement: SELL 거래 처리
SpotWallet MUST process SELL trades by removing assets from PairStack (FIFO) and adding quote currency.

#### Scenario: SELL 거래 처리
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BUY: 1.0 BTC at 50000
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(buy_trade)

# SELL: 0.6 BTC at 55000
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.6), Token("USD", 33000.0)),
    timestamp=1234567900
)
wallet.process_trade(sell_trade)

# USD 잔액: 100000 - 50000 + 33000 = 83000
assert wallet.get_currency_balance("USD") == 83000.0

# PairStack 확인: 0.4 BTC 남음
pair_stack = wallet.get_pair_stack("BTC-USD")
assert pair_stack.total_asset_amount() == 0.4
assert pair_stack.total_value_amount() == 20000.0

# Ledger 확인: realized PnL 기록
ledger = wallet.get_ledger("BTC-USD")
df = ledger.to_dataframe()
assert len(df) == 2
assert df.iloc[1]["side"] == "sell"
assert df.iloc[1]["realized_pnl"] == 3000.0  # (55000 - 50000) * 0.6
```

#### Scenario: 자산 부족으로 SELL 실패
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BUY: 1.0 BTC
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(buy_trade)

# SELL 시도: 2.0 BTC (보유량 초과)
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 2.0), Token("USD", 100000.0)),
    timestamp=1234567900
)

try:
    wallet.process_trade(sell_trade)
    assert False, "Should raise error"
except ValueError as e:
    assert "insufficient" in str(e).lower() or "exceeds" in str(e).lower()
```

#### Scenario: 전체 포지션 청산
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BUY: 1.0 BTC at 50000
buy_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-1",
    fill_id="fill-1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(buy_trade)

# SELL: 전체 1.0 BTC at 55000
sell_trade = SpotTrade(
    stock_address=stock_address,
    trade_id="trade-2",
    fill_id="fill-2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 1.0), Token("USD", 55000.0)),
    timestamp=1234567900
)
wallet.process_trade(sell_trade)

# USD 잔액: 100000 - 50000 + 55000 = 105000
assert wallet.get_currency_balance("USD") == 105000.0

# PairStack: 청산되어 None 또는 empty
pair_stack = wallet.get_pair_stack("BTC-USD")
assert pair_stack is None or pair_stack.is_empty()

# Ledger는 여전히 존재
ledger = wallet.get_ledger("BTC-USD")
assert ledger is not None
df = ledger.to_dataframe()
assert len(df) == 2
```

### Requirement: 조회 메서드
SpotWallet MUST provide query methods for currencies, pair stacks, and ledgers.

#### Scenario: 화폐 목록 조회
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=10000.0)
wallet.deposit_currency(symbol="KRW", amount=1000000.0)

currencies = wallet.list_currencies()
assert "USD" in currencies
assert "KRW" in currencies
assert len(currencies) == 2
```

#### Scenario: 티커 목록 조회
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BTC 매수
btc_trade = SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1",
    fill_id="f1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(btc_trade)

# ETH 매수
eth_trade = SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "eth", "usd", "1d"),
    trade_id="t2",
    fill_id="f2",
    side=SpotSide.BUY,
    pair=Pair(Token("ETH", 10.0), Token("USD", 20000.0)),
    timestamp=1234567900
)
wallet.process_trade(eth_trade)

tickers = wallet.list_tickers()
assert "BTC-USD" in tickers
assert "ETH-USD" in tickers
assert len(tickers) == 2
```

#### Scenario: 존재하지 않는 PairStack 조회
```python
wallet = SpotWallet()

pair_stack = wallet.get_pair_stack("BTC-USD")
assert pair_stack is None
```

#### Scenario: 존재하지 않는 Ledger 조회
```python
wallet = SpotWallet()

ledger = wallet.get_ledger("BTC-USD")
assert ledger is None
```

### Requirement: 문자열 표현
SpotWallet MUST provide readable string representations.

#### Scenario: SpotWallet 문자열 출력
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=10000.0)

wallet_str = str(wallet)
assert "SpotWallet" in wallet_str or "wallet" in wallet_str.lower()
assert "USD" in wallet_str or "usd" in wallet_str.lower()
```
