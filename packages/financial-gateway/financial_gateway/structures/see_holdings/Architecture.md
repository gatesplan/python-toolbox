# see_holdings Request/Response 설계

## 개요

보유 자산(거래 대상 자산) 조회 요청의 파라미터 및 응답 구조를 정의한다. 이 문서는 구체 Gateway Worker 구현 시 Request → API params 인코딩 및 API response → Response 디코딩 지침을 제공한다.

## see_holdings Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 선택 필드

**필터링:**
- `symbols: Optional[List[Symbol]]` - 조회할 거래쌍 목록 (None이면 전체 조회)

**필터링 동작:**
- `symbols=None`: 보유량이 0.001 미만인 자산 제외하고 모든 보유 자산 반환
- `symbols=[Symbol("BTC/USDT"), Symbol("ETH/BTC")]`: 해당 자산(base)만 조회
  - 보유량이 0이어도 포함 (0으로 표시)
  - Symbol의 quote가 unit_currency로 사용됨
- `symbols=[]`: 빈 리스트는 None과 동일하게 처리

## see_holdings Response 구조

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

**holdings 필드** (`dict[str, dict[str, Union[Pair, float]]]`):

```python
{
  "BTC": {
    "balance": Pair(
      asset=Token("BTC", 0.5),
      value=Token("KRW", 50000000)
    ),
    "available": 0.3,
    "promised": 0.2
  },
  "ETH": {
    "balance": Pair(
      asset=Token("ETH", 10),
      value=Token("KRW", 60000000)
    ),
    "available": 7.0,
    "promised": 3.0
  }
}
```

**각 자산별 구조:**
- `balance`: Pair 객체 (financial-assets)
  - `asset`: Token - 보유 자산 (symbol.base, 총 수량)
  - `value`: Token - 평단가 환산 가치 (symbol.quote, 총 가치)
- `available`: float - 거래 가능 수량
- `promised`: float - 주문/출금 등에 묶여 있는 수량

**수량 관계:**
- `asset.amount = available + promised`
- `value.amount = asset.amount × avg_buy_price`
- `value.symbol = symbol.quote` (Symbol에서 quote 사용)

### 실패 시 에러 코드

**인증/권한 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 자산 조회 권한 없음

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼 (특정 심볼 조회 시)

## 설계 원칙

### currencies 기준 분리
- Gateway 초기화 시 지정한 `currencies`는 holdings에서 제외
- 예: `currencies=["KRW"]`이면 KRW는 see_balance로 조회, 나머지는 holdings로 조회

### Symbol과 Pair의 관계
- Symbol.quote가 Pair의 value.symbol이 됨
- `Symbol("BTC/USDT")` → Pair(Token("BTC", ...), Token("USDT", ...))
- `Symbol("ETH/BTC")` → Pair(Token("ETH", ...), Token("BTC", ...))

**symbols=None (전체 조회) 시:**
- 거래소의 기본 quote currency 사용
- Upbit: KRW 기준 Pair 반환
- Binance: USDT 기준 Pair 반환
- Worker 구현에서 거래소별 기본값 결정

### 평단가 계산 책임
- holdings 응답은 항상 Pair 구조
- 거래소가 평단가를 직접 제공하면 → 그대로 사용
- 거래소가 평단가를 제공하지 않으면 → Gateway가 다른 API 조합하여 계산
  - 예: 거래 내역(trades) API 조회
  - 매수 체결 내역으로 가중평균 매수가 계산
  - 계산된 평단가로 Pair 생성

**거래소 지원 전제 조건:**
- 평단가 직접 제공 또는 거래 내역 API 제공 필수
- 위 조건을 충족하지 못하는 거래소는 지원하지 않음

### 0 잔고 처리
- `symbols=None`일 때: 0.001 미만인 잔고 자동 제외 (dust 제거)
- `symbols=[Symbol(...), ...]` 지정 시: 0 잔고여도 포함 (0으로 표시)
