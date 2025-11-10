# tradesim 모듈 구조

Backend 프로토콜을 준수하는 5계층 구조로 설계되었다.

## 계층 구조

### 입자층 (InternalStruct, Constants)
- **TradeParams**: Worker가 생성하는 체결 파라미터
- **FillProbability**: 체결 확률 상수
- **SplitConfig**: 수량 분할 설정 상수

### Core층
상호 의존성이 없는 순수 계산 함수들. 재사용성이 높다.
- **MathUtils**: 순수 수학 연산
- **CandleAnalyzer**: 캔들 영역 분석
- **PriceSampler**: 가격 샘플링 및 통계 계산
- **SlippageCalculator**: 슬리피지 범위 계산
- **AmountSplitter**: 수량 분할

### Service층
Core를 조합하여 비즈니스 로직을 구현. 서비스 간 독립적이다.
- **SpotLimitFillService**: 지정가 체결
- **SpotMarketBuyFillService**: 시장가 매수 체결
- **SpotMarketSellFillService**: 시장가 매도 체결
- **SpotTradeFactoryService**: Trade 객체 생성

### API층
외부 진입점. Service들을 오케스트레이션한다.
- **TradeSimulation**: 거래 시뮬레이션 API


## 외부 인터페이스

`TradeSimulation.process(order: Order, price: Price) -> List[Trade]`

Order와 Price를 받아 체결된 Trade 리스트를 반환한다.
