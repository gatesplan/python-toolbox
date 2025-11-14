# binance_spot 모듈 구조

Binance Spot 거래소 API와 통신하는 Gateway 구현체. CPSCP 패턴 기반 5계층 구조로 설계되었다.

**is_realworld_gateway**: True (API 키 검증 필수)

## 계층 구조

### Controller 계층 (API/)
- **BinanceSpotGateway**: SpotMarketGatewayBase 구현, Binance Spot API 통신 진입점

### Service 계층
비즈니스 워크플로우를 조율하며, Core 계층을 조합하여 완전한 요청-응답 사이클을 구성한다.

- **OrderRequestService**: 주문 요청 처리 (limit/market 주문 생성)
- **OrderQueryService**: 주문 조회 (주문 상태, 취소, 체결 내역)
- **BalanceService**: 계정 정보 조회 (잔고)
- **MarketDataService**: 시장 데이터 조회 (캔들, 호가, 시세)

### Core 계층
순수 변환/파싱 로직을 담당한다. Stateless로 설계되어 재사용성이 높다.

- **RequestConverter**: Request 객체 → Binance API 파라미터 변환
- **ResponseParser**: Binance API 응답 → Response 객체 파싱
- **APICallExecutor**: binance-connector 라이브러리로 실제 API 호출

### Particles 계층
상수, 설정, 데이터 구조를 정의한다.

- **Constants/**: Binance API 엔드포인트, 설정 상수
- **InternalStruct/**: API 파라미터 중간 데이터 구조

## 외부 인터페이스

SpotMarketGatewayBase 인터페이스를 모두 구현:
- 주문 관리: request_limit_buy_order, request_market_sell_order 등
- 계정 정보: request_current_balance, request_trade_history
- 시장 데이터: request_ticker, request_orderbook, request_candles
- 시스템 정보: request_available_markets, request_server_time

## 의존성

```
Particles (binance_endpoints, binance_config, api_params)
    ↑
Core (RequestConverter, ResponseParser, APICallExecutor)
    ↑
Service (OrderRequestService, BalanceService, MarketDataService)
    ↑
Controller (BinanceSpotGateway)
```

## 환경변수 요구사항

```
BINANCE_SPOT_API_KEY=your_api_key
BINANCE_SPOT_API_SECRET=your_api_secret
```

초기화 시 환경변수가 없으면 `EnvironmentError` 발생.
