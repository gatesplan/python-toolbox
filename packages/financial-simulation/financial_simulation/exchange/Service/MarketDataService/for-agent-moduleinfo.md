# MarketDataService

시장 데이터 기반 조회 및 변환 서비스. MarketData의 원시 데이터를 Gateway API 호환 형식으로 변환한다.

## 책임

- OHLC 기반 더미 호가창 생성
- 마켓 목록 조회 (Symbol + MarketStatus)
- 시장 데이터 조회 관련 비즈니스 로직 집중

## 의존성

- MarketData: 원시 시장 데이터 제공

## 메서드

### generate_orderbook(symbol: str | Symbol, depth: int = 20) -> Orderbook
    OHLC 기반 더미 호가창 생성 (Gateway API 호환용)

    Args:
        symbol: 심볼 (예: "BTC/USDT") 또는 Symbol 객체
        depth: 호가 깊이 (기본값: 20)

    Returns:
        Orderbook: financial-assets Orderbook 객체

    동작:
        1. MarketData에서 현재 OHLC 조회
        2. High-Low로 변동성 추정
        3. 변동성 기반 스프레드 계산
        4. depth만큼 bids/asks 생성 (멱함수 수량 분포)

### get_available_markets() -> list[dict]
    마켓 목록 조회 (Gateway API 호환용)

    Returns:
        list[dict]: [{"symbol": Symbol, "status": MarketStatus}, ...]

    동작:
        1. MarketData.get_symbols() 호출
        2. 각 심볼을 Symbol 객체로 변환
        3. 모든 마켓에 MarketStatus.TRADING 할당 (시뮬레이션 특성)

## Symbol 지원

`generate_orderbook()` 메서드는 `str | Symbol` 타입 지원:
- str: "BTC/USDT" (slash 형식)
- Symbol: Symbol("BTC/USDT") 또는 Symbol("BTC-USDT")

MarketData가 Symbol 지원하므로 별도 변환 없이 직접 전달.

---

## 설계 원칙

### Service Layer 역할
- MarketData는 원시 데이터만 관리 (Core Layer)
- MarketDataService는 비즈니스 로직 및 변환 담당 (Service Layer)
- SpotExchange는 진입점만 (API Layer)

### Gateway API 호환
- financial-gateway 요구사항에 맞춰 데이터 형식 변환
- Orderbook, Symbol, MarketStatus 등 도메인 객체 생성

### 확장 가능성
- 향후 get_ticker(), get_market_summary() 등 추가 가능
- 시장 데이터 조회 관련 로직은 모두 이 Service에 집중
