# API 계층 (Controller)

Binance Spot Gateway의 진입점. SpotMarketGatewayBase 인터페이스를 구현하여 전략 실행자에게 통일된 API를 제공한다.

## BinanceSpotGateway

Binance Spot 거래소와 통신하는 Controller. Service 계층을 조율하여 요청을 처리한다.

**책임:**
- SpotMarketGatewayBase 인터페이스 구현
- API 키 검증 (.env에서 BINANCE_SPOT_API_KEY, BINANCE_SPOT_API_SECRET 로드)
- Service 계층 생성 및 메서드 라우팅
- 에러 핸들링 및 최종 Response 반환
