# OrderValidator
주문 실행 전 거래소 컨텍스트 검증. 자금 충분성, 자산 보유량을 검증.

_portfolio: Portfolio       # 자산 및 잔고 조회용
_market_data: MarketData    # MARKET 주문 시 현재가 조회용

validate_order(order: SpotOrder) -> None
    raise ValueError
    주문 실행 전 거래소 컨텍스트 검증 (잔고/자산 충분성)

---

**검증 책임:**
- 주문 필드 자체는 SpotOrder 생성 시 이미 검증됨 (financial-assets 패키지 내부)
- OrderValidator는 거래소 컨텍스트만 검증 (잔고/자산 충분성, 미체결 주문 고려)
