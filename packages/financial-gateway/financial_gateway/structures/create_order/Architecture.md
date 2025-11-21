# create_order Request/Response 설계

## 개요

주문 생성 요청의 파라미터 및 응답 구조를 정의한다. 이 문서는 구체 Gateway Worker 구현 시 Request → API params 인코딩 및 API response → Response 디코딩 지침을 제공한다.

## create_order Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 주문 필수 필드

**거래 대상:**
- `address: StockAddress` - 거래할 자산 주소 (financial-assets)

**주문 기본 정보:**
- `side: OrderSide` - BUY / SELL (financial-assets enum)
- `order_type: OrderType` - LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT (financial-assets enum)

**수량/가격:**
- `asset_quantity: Optional[float]` - 주문 수량 (자산 단위)
- `price: Optional[float]` - 주문 가격 (인용 자산 단위)
- `quote_quantity: Optional[float]` - 인용 자산 수량 (시장가 매수 시)
- `stop_price: Optional[float]` - 트리거 가격 (스톱 주문 시)

### 주문 선택 필드

**체결 조건:**
- `time_in_force: Optional[TimeInForce]` - GTC, IOC, FOK (financial-assets enum, 기본값: GTC)
- `post_only: bool` - Maker 전용 주문 여부 (기본값: False)

**자전거래 방지:**
- `self_trade_prevention: Optional[SelfTradePreventionMode]` - NONE, CANCEL_MAKER, CANCEL_TAKER, CANCEL_BOTH (기본값: None)

**클라이언트 주문 ID:**
- `client_order_id: Optional[str]` - 사용자 정의 주문 ID (기본값: None, 없으면 request_id 사용)

### 주문 타입별 필수 파라미터

| order_type | 필수 파라미터 |
|-----------|-------------|
| LIMIT | asset_quantity, price |
| MARKET (매수) | asset_quantity 또는 quote_quantity |
| MARKET (매도) | asset_quantity |
| STOP_LOSS | asset_quantity, stop_price |
| STOP_LOSS_LIMIT | asset_quantity, price, stop_price |
| TAKE_PROFIT | asset_quantity, stop_price |
| TAKE_PROFIT_LIMIT | asset_quantity, price, stop_price |

## create_order Response 구조

### 공통 필드 (Response Base)
- `request_id`: 원본 요청 참조
- `is_success`: 성공/실패
- `send_when`: UTC ms
- `receive_when`: UTC ms
- `processed_when`: UTC ms (서버 처리 시각)
- `timegaps`: ms
- `error_code`: 에러 코드 (실패 시)
- `error_message`: 에러 메시지 (실패 시)

### 성공 시 응답 데이터

**주문 정보:**
- `order_id: str` - 거래소 발급 주문 ID
- `client_order_id: str` - 클라이언트 주문 ID
- `status: OrderStatus` - NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED 등
- `created_at: int` - 주문 생성 시각 (UTC ms, from server)

**체결 정보 (전체 또는 일부 체결 시):**
- `trades: List[Trade]` - 체결 내역 리스트 (financial-assets의 SpotTrade 또는 FuturesTrade)
- 실제 수수료는 Trade.fee에 기록됨 (Token 타입)

### 실패 시 에러 코드

**공통 에러:**
- `INVALID_PARAMETERS` - 잘못된 파라미터 (누락, 타입 오류 등)
- `INSUFFICIENT_BALANCE` - 잔고 부족
- `INVALID_QUANTITY` - 잘못된 수량 (최소/최대 범위, 소수점 자리수)
- `INVALID_PRICE` - 잘못된 가격 (최소/최대 범위, 소수점 자리수)
- `MARKET_CLOSED` - 마켓 거래 정지
- `INVALID_SYMBOL` - 존재하지 않는 심볼
- `SELF_TRADE_REJECTED` - 자전거래 방지로 거부

**주문 타입별 에러:**
- `POST_ONLY_REJECTED` - post_only 주문이 즉시 체결되어 거부
- `IOC_NO_FILL` - IOC 주문이 즉시 체결되지 않아 취소
- `FOK_NO_FULL_FILL` - FOK 주문이 전량 체결되지 않아 거부
- `STOP_PRICE_INVALID` - 트리거 가격이 현재가와 역방향
