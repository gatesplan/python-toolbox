# see_holdings Request/Response 설계

## 개요

보유 자산(거래 대상 자산) 조회 요청의 파라미터 및 응답 구조를 정의한다. 이 문서는 구체 Gateway Worker 구현 시 Request → API params 인코딩 및 API response → Response 디코딩 지침을 제공한다.

## see_holdings Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 선택 필드

**필터링:**
- `symbols: Optional[List[str]]` - 조회할 자산 심볼 목록 (None이면 전체 조회)

**필터링 동작:**
- `symbols=None`: 보유량이 0 또는 거의 0인 자산 제외하고 모든 보유 자산 반환
- `symbols=["BTC", "ETH"]`: 해당 심볼만 조회, 보유하지 않으면 결과에서 제외
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
  - `asset`: Token - 보유 자산 (심볼, 총 수량)
  - `value`: Token - 평단가 환산 가치 (거래소가 제공하는 unit_currency 기준)
- `available`: float - 거래 가능 수량
- `promised`: float - 주문/출금 등에 묶여 있는 수량

**수량 관계:**
- `asset.amount = available + promised`
- `value.amount = asset.amount × avg_buy_price`

**Pair의 value.symbol:**
- 거래소 API가 제공하는 unit_currency 그대로 사용
- 예: Upbit에서 ETH의 `unit_currency="BTC"`면 → Pair의 value는 Token("BTC", ...)

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

### 실제 거래 쌍 그대로 반환
- Pair는 거래소 API가 제공하는 실제 거래 쌍(unit_currency) 그대로 사용
- Gateway는 Pair 변환이나 환산을 하지 않음
- 예: Upbit에서 ETH의 `unit_currency="BTC"`면 → Pair(Token("ETH", ...), Token("BTC", ...))

**예시:**
```
// Upbit API 응답
{
  "currency": "XYZ",
  "unit_currency": "BTC",  // XYZ/BTC 거래 쌍
  "balance": "100",
  "avg_buy_price": "0.001"
}

// holdings 변환
{
  "XYZ": {
    "balance": Pair(Token("XYZ", 100), Token("BTC", 0.1)),  // 실제 쌍 그대로
    "available": 100.0,
    "promised": 0.0
  }
}
```

**환산이 필요한 경우:**
- Gateway 책임 아님
- 사용자가 Gateway의 시세 조회 API를 사용하여 직접 환산

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
- `symbols=None`일 때: 0 또는 거의 0인 잔고 자동 제외
- `symbols=[...]` 지정 시: 0 잔고여도 조회 시도, 보유 안 하면 결과에서 제외

## 거래소별 매핑 예시

### Upbit
```json
// API 응답
[
  {
    "currency": "BTC",
    "balance": "0.5",
    "locked": "0.2",
    "avg_buy_price": "100000000",
    "unit_currency": "KRW"  // BTC/KRW 거래 쌍
  },
  {
    "currency": "XYZ",
    "balance": "100",
    "locked": "0",
    "avg_buy_price": "0.001",
    "unit_currency": "BTC"  // XYZ/BTC 거래 쌍
  }
]

// holdings 변환 (currencies=["KRW"])
{
  "BTC": {
    "balance": Pair(Token("BTC", 0.5), Token("KRW", 50000000)),  // unit_currency 그대로
    "available": 0.3,
    "promised": 0.2
  },
  "XYZ": {
    "balance": Pair(Token("XYZ", 100), Token("BTC", 0.1)),  // unit_currency 그대로
    "available": 100.0,
    "promised": 0.0
  }
}
```

### Binance
```json
// 1단계: 잔고 조회 API 응답
{
  "balances": [
    {
      "asset": "BTC",
      "free": "0.3",
      "locked": "0.2"
    },
    {
      "asset": "ETH",
      "free": "7.0",
      "locked": "3.0"
    }
  ]
}

// 2단계: 평단가가 없으므로 거래 내역 조회
// GET /api/v3/myTrades?symbol=BTCUSDT
[
  {
    "price": "120000000",
    "qty": "0.3",
    "quoteQty": "36000000",
    "isBuyer": true
  },
  {
    "price": "115000000",
    "qty": "0.2",
    "quoteQty": "23000000",
    "isBuyer": true
  }
]

// 3단계: 가중평균 매수가 계산
// BTC 평단가 = (36000000 + 23000000) / (0.3 + 0.2) = 118000000 USDT/BTC

// 4단계: holdings 변환 (currencies=["USDT"])
{
  "BTC": {
    "balance": Pair(Token("BTC", 0.5), Token("USDT", 59000000)),  // 계산된 평단가
    "available": 0.3,
    "promised": 0.2
  },
  "ETH": {
    "balance": Pair(Token("ETH", 10), Token("USDT", 60000000)),  // 계산된 평단가
    "available": 7.0,
    "promised": 3.0
  }
}
```

**참고**: Binance처럼 잔고 조회에서 평단가를 제공하지 않는 거래소의 경우, Gateway 내부에서 거래 내역 API를 추가로 호출하여 평단가를 계산합니다.
