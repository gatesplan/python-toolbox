# simulation_spot 모듈 구조

시뮬레이션 환경(financial-simulation.exchange.SpotExchange)과 연동하는 Gateway 구현체. CPSCP 패턴 기반 계층 구조로 설계되었다.

**is_realworld_gateway**: False (API 키 검증 불필요)

## 계층 구조

### Controller 계층 (API/)
- **SimulationSpotGateway**: SpotMarketGatewayBase 구현, 시뮬레이션 환경 진입점

### Service 계층
시뮬레이션 환경에서는 거래소 API 호출이 아닌 SpotExchange 메서드 호출로 동작한다.

- **OrderPlacementService**: 주문 실행 (SpotExchange.place_order() 호출)
- **OrderQueryService**: 주문 조회 (SpotExchange에서 주문 상태 조회)
- **BalanceService**: 잔고 조회 (시뮬레이션 계정 잔고)

### Core 계층
시뮬레이션 환경에 특화된 Core 계층.

- **OrderFactory**: Request → SpotOrder 객체 생성
- **ResponseBuilder**: SpotTrade/SpotOrder → Response 객체 생성

### Particles 계층
- **InternalStruct/**: 시뮬레이션 상태 데이터 구조

## 외부 인터페이스

SpotMarketGatewayBase 인터페이스를 모두 구현.

## 의존성

```
Particles (simulation_state)
    ↑
Core (OrderFactory, ResponseBuilder)
    ↑
Service (OrderPlacementService, OrderQueryService, BalanceService)
    ↑
Controller (SimulationSpotGateway)
    ↑
SpotExchange (financial-simulation.exchange)
```

## 초기화

```python
from financial_simulation.exchange import SpotExchange
from financial_gateway.simulation_spot.API.SimulationSpotGateway import SimulationSpotGateway

spot_exchange = SpotExchange(...)
gateway = SimulationSpotGateway(spot_exchange)
```

SpotExchange 인스턴스를 주입받아 초기화한다. 환경변수 검증 없음.

## 시뮬레이션 특징

- API 키 불필요
- SpotExchange에 직접 주문 제출
- Order 객체를 내부에서 생성하여 SpotExchange에 전달
- SpotExchange가 반환한 list[SpotTrade]를 Response로 변환
- 시장 데이터는 시뮬레이션 환경의 가상 데이터 제공
