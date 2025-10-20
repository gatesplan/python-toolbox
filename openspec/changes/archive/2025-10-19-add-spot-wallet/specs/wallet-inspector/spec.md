# wallet-inspector Specification

## Purpose
SpotWallet의 통계 및 분석 기능을 제공하는 WalletInspector 모듈을 정의합니다. Director-Worker 패턴을 사용하여 확장 가능한 구조로 설계되며, 각 Worker는 특정 분석 작업을 담당합니다.

## ADDED Requirements

### Requirement: WalletInspector Director 클래스
WalletInspector MUST act as a director that coordinates analysis workers to provide wallet statistics.

#### Scenario: WalletInspector 초기화
```python
from financial_assets.wallet import SpotWallet, WalletInspector

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# Inspector 생성
inspector = WalletInspector(wallet)

# Inspector는 wallet 참조를 유지
assert inspector.wallet is wallet
```

### Requirement: 총 자산 가치 계산
WalletInspector MUST calculate total portfolio value in a specified quote currency using current market prices.

#### Scenario: 총 자산 가치 조회 (화폐만)
```python
from financial_assets.wallet import SpotWallet, WalletInspector

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=50000.0)
wallet.deposit_currency(symbol="KRW", amount=1000000.0)

inspector = WalletInspector(wallet)

# USD 기준 총 자산 (USD만, 자산 없음)
total = inspector.get_total_value(quote_symbol="USD", current_prices={})
assert total == 50000.0
```

#### Scenario: 총 자산 가치 조회 (자산 포함)
```python
from financial_assets.wallet import SpotWallet, WalletInspector
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BTC 매수: 1.0 BTC at 50000
stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
trade = SpotTrade(
    stock_address=stock_address,
    trade_id="t1",
    fill_id="f1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(trade)

inspector = WalletInspector(wallet)

# 현재 BTC 가격 (Price 객체의 close 사용)
btc_price = Price(
    exchange="binance",
    market="BTC/USD",
    t=1234567900,
    h=56000.0,
    l=54000.0,
    o=54500.0,
    c=55000.0,  # close 가격이 현재가
    v=1000.0
)

# USD: 50000, BTC: 1.0 * 55000 (close) = 55000
# Total: 105000
current_prices = {"BTC-USD": btc_price}
total = inspector.get_total_value(quote_symbol="USD", current_prices=current_prices)
assert total == 105000.0
```

#### Scenario: 여러 자산 총 가치 계산
```python
from financial_assets.price import Price

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

inspector = WalletInspector(wallet)

# 현재 가격 (Price 객체)
btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
eth_price = Price("binance", "ETH/USD", 1234567910, 2600.0, 2400.0, 2450.0, 2500.0, 5000.0)

current_prices = {"BTC-USD": btc_price, "ETH-USD": eth_price}
# USD: 30000, BTC: 1.0 * 55000 = 55000, ETH: 10.0 * 2500 = 25000
# Total: 110000
total = inspector.get_total_value(quote_symbol="USD", current_prices=current_prices)
assert total == 110000.0
```

### Requirement: 실현 손익 계산
WalletInspector MUST calculate total realized profit/loss from all ledgers.

#### Scenario: 총 실현 손익 조회
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BUY: 1.0 BTC at 50000
buy_trade = SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1",
    fill_id="f1",
    side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
)
wallet.process_trade(buy_trade)

# SELL: 0.6 BTC at 55000
sell_trade = SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t2",
    fill_id="f2",
    side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.6), Token("USD", 33000.0)),
    timestamp=1234567900
)
wallet.process_trade(sell_trade)

inspector = WalletInspector(wallet)

# 실현 손익: (55000 - 50000) * 0.6 = 3000
total_pnl = inspector.get_total_realized_pnl()
assert total_pnl == 3000.0
```

#### Scenario: 여러 거래쌍의 실현 손익 합계
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=200000.0)

# BTC 거래
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1", fill_id="f1", side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
))
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t2", fill_id="f2", side=SpotSide.SELL,
    pair=Pair(Token("BTC", 0.5), Token("USD", 27500.0)),
    timestamp=1234567900
))

# ETH 거래
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "eth", "usd", "1d"),
    trade_id="t3", fill_id="f3", side=SpotSide.BUY,
    pair=Pair(Token("ETH", 10.0), Token("USD", 20000.0)),
    timestamp=1234567910
))
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "eth", "usd", "1d"),
    trade_id="t4", fill_id="f4", side=SpotSide.SELL,
    pair=Pair(Token("ETH", 5.0), Token("USD", 11000.0)),
    timestamp=1234567920
))

inspector = WalletInspector(wallet)

# BTC PnL: (55000 - 50000) * 0.5 = 2500
# ETH PnL: (2200 - 2000) * 5 = 1000
# Total: 3500
total_pnl = inspector.get_total_realized_pnl()
assert total_pnl == 3500.0
```

### Requirement: 미실현 손익 계산
WalletInspector MUST calculate unrealized profit/loss for current positions using current market prices.

#### Scenario: 미실현 손익 조회
```python
from financial_assets.price import Price

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BUY: 1.0 BTC at 50000
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1", fill_id="f1", side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
))

inspector = WalletInspector(wallet)

# 현재 가격 (Price 객체)
btc_price = Price("binance", "BTC/USD", 1234567900, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)

# (55000 - 50000) * 1.0 = 5000
current_prices = {"BTC-USD": btc_price}
unrealized_pnl = inspector.get_unrealized_pnl(quote_symbol="USD", current_prices=current_prices)
assert unrealized_pnl == 5000.0
```

#### Scenario: 여러 자산 미실현 손익
```python
from financial_assets.price import Price

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=100000.0)

# BTC: 1.0 at 50000
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1", fill_id="f1", side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
))

# ETH: 10.0 at 20000
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "eth", "usd", "1d"),
    trade_id="t2", fill_id="f2", side=SpotSide.BUY,
    pair=Pair(Token("ETH", 10.0), Token("USD", 20000.0)),
    timestamp=1234567900
))

inspector = WalletInspector(wallet)

# 현재 가격 (Price 객체)
btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
eth_price = Price("binance", "ETH/USD", 1234567910, 1900.0, 1700.0, 1750.0, 1800.0, 10000.0)

# BTC: (55000 - 50000) * 1.0 = 5000
# ETH: (1800 - 2000) * 10.0 = -2000
# Total: 3000
current_prices = {"BTC-USD": btc_price, "ETH-USD": eth_price}
unrealized_pnl = inspector.get_unrealized_pnl(quote_symbol="USD", current_prices=current_prices)
assert unrealized_pnl == 3000.0
```

### Requirement: 포지션 요약 DataFrame
WalletInspector MUST provide a position summary as a DataFrame with ticker, amount, cost basis, current value, and unrealized PnL.

#### Scenario: 포지션 요약 조회
```python
from financial_assets.price import Price

wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=200000.0)

# BTC 매수
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "btc", "usd", "1d"),
    trade_id="t1", fill_id="f1", side=SpotSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890
))

# ETH 매수
wallet.process_trade(SpotTrade(
    stock_address=StockAddress("crypto", "binance", "spot", "eth", "usd", "1d"),
    trade_id="t2", fill_id="f2", side=SpotSide.BUY,
    pair=Pair(Token("ETH", 10.0), Token("USD", 20000.0)),
    timestamp=1234567900
))

inspector = WalletInspector(wallet)

# 현재 가격 (Price 객체)
btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
eth_price = Price("binance", "ETH/USD", 1234567910, 1900.0, 1700.0, 1750.0, 1800.0, 10000.0)

current_prices = {"BTC-USD": btc_price, "ETH-USD": eth_price}
df = inspector.get_position_summary(quote_symbol="USD", current_prices=current_prices)

# DataFrame 컬럼 확인
assert "ticker" in df.columns
assert "asset_amount" in df.columns
assert "avg_price" in df.columns
assert "cost_basis" in df.columns
assert "current_value" in df.columns
assert "unrealized_pnl" in df.columns

# BTC 행 확인
btc_row = df[df["ticker"] == "BTC-USD"].iloc[0]
assert btc_row["asset_amount"] == 1.0
assert btc_row["avg_price"] == 50000.0
assert btc_row["cost_basis"] == 50000.0
assert btc_row["current_value"] == 55000.0
assert btc_row["unrealized_pnl"] == 5000.0

# ETH 행 확인
eth_row = df[df["ticker"] == "ETH-USD"].iloc[0]
assert eth_row["asset_amount"] == 10.0
assert eth_row["avg_price"] == 2000.0
assert eth_row["unrealized_pnl"] == -2000.0
```

### Requirement: 화폐 잔액 요약 DataFrame
WalletInspector MUST provide a currency balance summary as a DataFrame.

#### Scenario: 화폐 잔액 요약 조회
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=50000.0)
wallet.deposit_currency(symbol="KRW", amount=1000000.0)

inspector = WalletInspector(wallet)

df = inspector.get_currency_summary()

# DataFrame 컬럼 확인
assert "symbol" in df.columns
assert "amount" in df.columns

# USD 행 확인
usd_row = df[df["symbol"] == "USD"].iloc[0]
assert usd_row["amount"] == 50000.0

# KRW 행 확인
krw_row = df[df["symbol"] == "KRW"].iloc[0]
assert krw_row["amount"] == 1000000.0
```

### Requirement: Worker 확장 가능성
WalletInspector MUST support adding custom analysis workers through a defined interface.

#### Scenario: Worker 인터페이스 정의
```python
from financial_assets.wallet.worker import WalletWorker
from financial_assets.wallet import SpotWallet

# Custom Worker 구현
class CustomAnalysisWorker(WalletWorker):
    def analyze(self, wallet: SpotWallet) -> dict:
        return {
            "currency_count": len(wallet.list_currencies()),
            "ticker_count": len(wallet.list_tickers())
        }

# Worker 등록 및 사용 (확장 가능)
wallet = SpotWallet()
worker = CustomAnalysisWorker()
result = worker.analyze(wallet)

assert "currency_count" in result
assert "ticker_count" in result
```

### Requirement: 문자열 표현
WalletInspector MUST provide readable string representations.

#### Scenario: WalletInspector 문자열 출력
```python
wallet = SpotWallet()
wallet.deposit_currency(symbol="USD", amount=10000.0)

inspector = WalletInspector(wallet)

inspector_str = str(inspector)
assert "WalletInspector" in inspector_str or "inspector" in inspector_str.lower()
```
