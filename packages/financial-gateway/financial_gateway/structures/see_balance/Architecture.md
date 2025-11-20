# see_balance Request/Response 설계

## 개요

현금 자산(reference currency) 조회 요청의 파라미터 및 응답 구조를 정의한다. 이 문서는 구체 Gateway Worker 구현 시 Request → API params 인코딩 및 API response → Response 디코딩 지침을 제공한다.

## see_balance Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 선택 필드

**필터링:**
- `currencies: Optional[List[str]]` - 조회할 현금 심볼 목록 (None이면 전체 조회)

**필터링 동작:**
- `currencies=None`: 보유량이 0 또는 거의 0인 현금 제외하고 모든 현금 자산 반환
- `currencies=["KRW", "USD"]`: 해당 현금만 조회, 보유하지 않으면 결과에서 제외
- `currencies=[]`: 빈 리스트는 None과 동일하게 처리

## see_balance Response 구조

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

**balances 필드** (`dict[str, dict[str, Union[Token, float]]]`):

```python
{
  "KRW": {
    "balance": Token("KRW", 1000000),
    "available": 800000.0,
    "promised": 200000.0
  },
  "USD": {
    "balance": Token("USD", 500),
    "available": 300.0,
    "promised": 200.0
  }
}
```

**각 현금별 구조:**
- `balance`: Token 객체 (financial-assets)
  - `symbol`: 현금 심볼
  - `amount`: 총 보유량
- `available`: float - 거래 가능 금액
- `promised`: float - 주문/출금 등에 묶여 있는 금액

**수량 관계:**
- `balance.amount = available + promised`

### 실패 시 에러 코드

**인증/권한 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 자산 조회 권한 없음

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

**데이터 에러:**
- `INVALID_CURRENCY` - 존재하지 않는 화폐 (특정 화폐 조회 시)

## 설계 원칙

### currencies만 포함
- Gateway 초기화 시 지정한 `currencies`만 balance로 조회
- 예: `currencies=["KRW"]`이면 KRW만 see_balance로 조회
- 예: `currencies=["USDT", "BUSD"]`이면 USDT, BUSD만 see_balance로 조회

### 평단가 없음
- 현금 자산은 평단가 개념이 없음
- Token으로 수량만 표현 (Pair 아님)
- 환율 변동은 별도 환거래 원장에서 추적

### 필수 교환 체인 무시
- 원 → 달러 → 나스닥 같은 필수 교환 체인은 Gateway 관심사 아님
- 달러도 하나의 현금 자산으로 취급
- 환율 손익은 별도 시스템에서 보정

### 0 잔고 처리
- `currencies=None`일 때: 0 또는 거의 0인 잔고 자동 제외
- `currencies=[...]` 지정 시: 0 잔고여도 조회 시도, 보유 안 하면 결과에서 제외

## 거래소별 매핑 예시

### Upbit
```json
// API 응답
[
  {
    "currency": "KRW",
    "balance": "1000000",
    "locked": "200000",
    "avg_buy_price": "0",
    "unit_currency": "KRW"
  }
]

// balance 변환 (currencies=["KRW"])
{
  "KRW": {
    "balance": Token("KRW", 1000000),
    "available": 800000.0,
    "promised": 200000.0
  }
}
```

### Binance
```json
// API 응답
{
  "balances": [
    {
      "asset": "USDT",
      "free": "800.0",
      "locked": "200.0"
    }
  ]
}

// balance 변환 (currencies=["USDT"])
{
  "USDT": {
    "balance": Token("USDT", 1000),
    "available": 800.0,
    "promised": 200.0
  }
}
```

## holdings vs balance 구분

### holdings (see_holdings)
- **대상**: 거래 자산 (주식, 암호화폐, 파생상품 등)
- **구조**: Pair (평단가 포함)
- **제외**: currencies

### balance (see_balance)
- **대상**: 현금 자산 (법정화폐, 스테이블코인 등)
- **구조**: Token (평단가 없음)
- **포함**: currencies만

### 예시 (currencies=["KRW"])

**보유 자산:**
- KRW 100만원
- BTC 0.5개 (평단가 1억)
- ETH 10개 (평단가 600만)

**see_holdings 응답:**
```python
{
  "BTC": { "balance": Pair(...), "available": 0.3, "promised": 0.2 },
  "ETH": { "balance": Pair(...), "available": 7.0, "promised": 3.0 }
}
```

**see_balance 응답:**
```python
{
  "KRW": { "balance": Token("KRW", 1000000), "available": 800000, "promised": 200000 }
}
```
