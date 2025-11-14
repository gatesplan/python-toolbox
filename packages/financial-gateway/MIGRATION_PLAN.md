# Financial Gateway CPSCP 마이그레이션 계획

## 현재 상태

**완료:**
- BaseGateway 구현 완료 (base/BaseGateway.py)
- 기본 테스트 코드 작성 완료

**미구현:**
- SpotMarketGatewayBase 인터페이스 (정의만 완료, 구현 필요)
- 모든 Gateway 구현체 (BinanceSpotGateway, UpbitSpotGateway, SimulationSpotGateway)

## 마이그레이션 전략

### 1단계: 인터페이스 레이어 완성
- [x] BaseGateway.py 유지
- [x] SpotMarketGatewayBase.py 생성 (추상 클래스)
- [x] base/ 폴더 moduleinfo 업데이트

### 2단계: 디렉토리 구조 생성
- [x] binance_spot/ CPSCP 계층 구조 생성
- [x] upbit_spot/ CPSCP 계층 구조 생성
- [x] simulation_spot/ CPSCP 계층 구조 생성

### 3단계: BinanceSpotGateway 구현 (우선순위 1)

**Controller (API/):**
- [ ] BinanceSpotGateway.py 구현
  - SpotMarketGatewayBase 상속
  - 환경변수 검증 (BINANCE_SPOT_API_KEY, BINANCE_SPOT_API_SECRET)
  - Service 계층 인스턴스 생성 및 메서드 라우팅

**Service:**
- [ ] OrderRequestService.py
- [ ] OrderQueryService.py
- [ ] BalanceService.py
- [ ] MarketDataService.py

**Core:**
- [ ] RequestConverter.py (정적 메서드, Request → API params)
- [ ] ResponseParser.py (정적 메서드, API response → Response)
- [ ] APICallExecutor.py (binance-connector 래핑)

**Particles:**
- [ ] Constants/binance_endpoints.py
- [ ] Constants/binance_config.py
- [ ] InternalStruct/api_params.py

**테스트:**
- [ ] test_binance_spot_gateway.py 업데이트

### 4단계: SimulationSpotGateway 구현 (우선순위 2)

**Controller (API/):**
- [ ] SimulationSpotGateway.py 구현
  - SpotMarketGatewayBase 상속
  - SpotExchange 인스턴스 주입
  - 환경변수 검증 없음 (is_realworld_gateway=False)

**Service:**
- [ ] OrderPlacementService.py (SpotExchange.place_order() 호출)
- [ ] OrderQueryService.py
- [ ] BalanceService.py

**Core:**
- [ ] OrderFactory.py (Request → SpotOrder)
- [ ] ResponseBuilder.py (SpotTrade/SpotOrder → Response)

**Particles:**
- [ ] InternalStruct/simulation_state.py

**테스트:**
- [ ] test_simulation_spot_gateway.py 업데이트

### 5단계: UpbitSpotGateway 구현 (우선순위 3)

Binance와 유사한 구조로 구현:
- [ ] Controller, Service, Core, Particles 계층 구현
- [ ] python-upbit-api 라이브러리 통합
- [ ] 환경변수 검증 (UPBIT_SPOT_API_KEY, UPBIT_SPOT_API_SECRET)
- [ ] 테스트 작성

### 6단계: 통합 테스트 및 문서화

- [ ] 전체 통합 테스트 작성
- [ ] 각 계층별 단위 테스트 보강
- [ ] README.md 업데이트
- [ ] 사용 예제 추가

## 구현 순서 근거

1. **BinanceSpotGateway 우선**: 가장 복잡하고 완전한 구현. 패턴 검증에 적합.
2. **SimulationSpotGateway**: 전략 테스트에 필수. BinanceSpotGateway 패턴을 참고하여 구현.
3. **UpbitSpotGateway**: Binance 패턴을 따르므로 구현 난이도 낮음.

## 기존 코드 처리

**유지:**
- `base/BaseGateway.py` - 변경 없음
- `.env.example` - 변경 없음
- `pyproject.toml` - 변경 없음

**대체:**
- `base/for-agent-moduleinfo.md` - 업데이트 완료
- `Architecture.md` - 전면 재작성 완료

**삭제 예정:**
- 기존 테스트 파일은 새 구조에 맞게 재작성 후 삭제

## 예상 일정

- 1-2단계: 완료
- 3단계 (BinanceSpotGateway): 2-3일
- 4단계 (SimulationSpotGateway): 1-2일
- 5단계 (UpbitSpotGateway): 1-2일
- 6단계 (테스트 및 문서화): 1일

**총 예상 기간: 5-8일**

## 주의사항

1. **인터페이스 호환성**: SpotMarketGatewayBase 인터페이스는 변경 금지
2. **환경변수 네이밍**: `{PROVIDER}_{MARKET_TYPE}_API_KEY/SECRET` 규칙 엄수
3. **에러 핸들링**: 각 Gateway별 적절한 예외 정의 및 처리
4. **로깅**: simple-logger 사용, 코딩 프로토콜 준수
5. **문서화**: 각 계층의 moduleinfo 문서 유지보수

## 롤백 계획

문제 발생 시:
1. base/ 폴더만 유지 (BaseGateway.py)
2. 새로 생성한 Gateway 모듈 폴더 삭제
3. Architecture.md git 복원

## 다음 단계

CPSCP 패턴 적용 후:
- FuturesMarketGatewayBase 설계
- BinanceFuturesGateway 구현
- 추가 거래소 지원 (Bybit, OKX 등)
