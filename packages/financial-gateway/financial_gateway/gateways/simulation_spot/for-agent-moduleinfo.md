# Simulation Spot Gateway

Simulation Spot 거래를 위한 Gateway Director. SpotExchange를 공유 리소스로 보유하며 Request를 적절한 Worker로 라우팅한다.

## SimulationSpotGateway

Simulation Spot Gateway Director (SDW 패턴의 Director)

exchange: SpotExchange  # 공유 리소스
_workers: Dict[Type[BaseRequest], object]  # Request 타입 → Worker 매핑

__init__(exchange: SpotExchange)
    SpotExchange를 받아 13개 Worker 인스턴스 생성
    Request 타입 → Worker 매핑 딕셔너리 구성

gateway_name: str
    "simulation_spot" 반환

is_realworld_gateway: bool
    False 반환 (시뮬레이션 Gateway)

async execute(request: BaseRequest) -> BaseResponse
    Request 타입에 따라 적절한 Worker로 라우팅
    Worker의 execute() 메서드 호출 (동기 함수)
    지원하지 않는 Request 타입이면 ValueError 발생

## 사용 예시

```python
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_gateway.gateways.simulation_spot import SimulationSpotGateway
from financial_gateway.structures.see_balance import SeeBalanceRequest

# Exchange 생성
exchange = SpotExchange(
    initial_balance=100000.0,
    market_data=market_data,
    maker_fee_ratio=0.001,
    taker_fee_ratio=0.002,
    quote_currency="USDT"
)

# Gateway 생성
gateway = SimulationSpotGateway(exchange)

# Request 실행
request = SeeBalanceRequest(
    request_id="req-001",
    gateway_name="simulation"
)
response = await gateway.execute(request)

# Response 확인
if response.is_success:
    print(response.balances)
```
