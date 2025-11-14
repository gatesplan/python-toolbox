# upbit_spot 모듈 구조

Upbit 거래소 API와 통신하는 Gateway 구현체. CPSCP 패턴 기반 5계층 구조로 설계되었다.

**is_realworld_gateway**: True (API 키 검증 필수)

## 계층 구조

### Controller 계층 (API/)
- **UpbitSpotGateway**: SpotMarketGatewayBase 구현, Upbit API 통신 진입점

### Service 계층
- **OrderRequestService**: 주문 요청 처리 (limit/market 주문 생성)
- **OrderQueryService**: 주문 조회 (주문 상태, 취소, 체결 내역)
- **BalanceService**: 계정 정보 조회 (잔고)
- **MarketDataService**: 시장 데이터 조회 (캔들, 호가, 시세)

### Core 계층
- **RequestConverter**: Request 객체 → Upbit API 파라미터 변환
- **ResponseParser**: Upbit API 응답 → Response 객체 파싱
- **APICallExecutor**: python-upbit-api 라이브러리로 실제 API 호출

### Particles 계층
- **Constants/**: Upbit API 엔드포인트, 설정 상수
- **InternalStruct/**: API 파라미터 중간 데이터 구조

## 외부 인터페이스

SpotMarketGatewayBase 인터페이스를 모두 구현.

## 의존성

```
Particles (upbit_endpoints, upbit_config, api_params)
    ↑
Core (RequestConverter, ResponseParser, APICallExecutor)
    ↑
Service (OrderRequestService, BalanceService, MarketDataService)
    ↑
Controller (UpbitSpotGateway)
```

## 환경변수 요구사항

```
UPBIT_SPOT_API_KEY=your_api_key
UPBIT_SPOT_API_SECRET=your_api_secret
```

초기화 시 환경변수가 없으면 `EnvironmentError` 발생.

## Upbit 특이사항

- 원화(KRW) 마켓 지원
- 주문 타입: 지정가, 시장가만 지원 (Stop 주문 미지원)
- API 요청 제한: 초당 10회, 분당 200회
