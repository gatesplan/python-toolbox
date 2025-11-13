# ValueCalculator
자산 가치 계산 로직 (Core Layer). Stateless 정적 메서드로 구성.

## 포지션 가치 계산

@staticmethod
calculate_position_book_value(pair_stack: PairStack | None) -> float
    포지션의 보유 가치 계산 (매수 당시 지불한 금액)

    Args:
        pair_stack: PairStack 인스턴스 (None 허용)

    Returns:
        float: 보유 가치 (PairStack.total_value_amount())

    Notes:
        - pair_stack이 None이거나 비어있으면 0.0 반환
        - Book Value = 매수 당시 지불한 총 금액
        - 평균 매입가 × 보유 수량과 동일

@staticmethod
calculate_position_market_value(amount: float, current_price: float) -> float
    포지션의 현재 시장 가치 계산

    Args:
        amount: 보유 수량
        current_price: 현재 시장 가격

    Returns:
        float: 현재 시장 가치 (amount × current_price)

    Notes:
        - amount나 current_price가 0이면 0.0 반환
        - Market Value = 현재 가격 × 보유 수량

## Currency 가치 계산

@staticmethod
calculate_currency_value(
    currencies: dict[str, float],
    quote_currency: str,
    market_data: MarketData
) -> float
    모든 Currency의 총 가치 계산 (quote_currency 기준)

    Args:
        currencies: {currency_symbol: amount} 형식
        quote_currency: 기준 화폐 (예: "USDT")
        market_data: MarketData 인스턴스 (현재 가격 조회용)

    Returns:
        float: Currency 총 가치 (quote_currency 기준)

    Notes:
        - quote_currency 자체는 1:1 계산
        - 다른 Currency는 symbol/quote_currency 형식으로 가격 조회
        - 예: BTC → BTC/USDT 가격 조회
        - 가격 데이터 없으면 해당 Currency는 0으로 처리

## 전체 가치 계산

@staticmethod
calculate_total_value(
    currency_value: float,
    position_market_values: dict[str, float]
) -> float
    총 자산 가치 계산 (Currency + Position)

    Args:
        currency_value: Currency 총 가치
        position_market_values: {ticker: market_value} 형식

    Returns:
        float: 총 자산 가치

    Notes:
        - 단순 합산: currency_value + sum(position_market_values.values())

---

**사용 예시:**
```python
# 포지션 보유 가치
pair_stack = portfolio.get_wallet().get_pair_stack("BTC-USDT")
book_value = ValueCalculator.calculate_position_book_value(pair_stack)  # 22500 USDT

# 포지션 현재 가치
amount = 0.5  # BTC
current_price = 50000.0  # USDT
market_value = ValueCalculator.calculate_position_market_value(amount, current_price)  # 25000 USDT

# Currency 총 가치
currencies = {"USDT": 10000.0, "BTC": 0.1}
currency_value = ValueCalculator.calculate_currency_value(
    currencies, "USDT", market_data
)  # 10000 + 0.1 * 50000 = 15000 USDT

# 전체 가치
total = ValueCalculator.calculate_total_value(
    currency_value=15000.0,
    position_market_values={"BTC-USDT": 25000.0}
)  # 40000 USDT
```

**의존성:**
- financial_assets.pair.PairStack: 보유 가치 조회
- MarketData: 현재 가격 조회

**계산 로직:**
- **Book Value**: PairStack에 저장된 매수 당시 지불 금액
- **Market Value**: 현재 시장 가격 × 보유 수량
- **Currency 가격 조회**: symbol/quote 형식 (예: BTC/USDT)
