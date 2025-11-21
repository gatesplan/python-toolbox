# UpbitSpotGateway 실거래 테스트

실제 Upbit API를 사용하여 UpbitSpotGateway의 모든 기능을 테스트합니다.

## 테스트 구성

### Phase 1: 읽기 전용 (안전) ✅
- 서버 시간 조회 (로컬 시간)
- XRP/KRW 시세 조회
- 호가창 조회
- 보유 자산 조회 (평단가 포함 - Upbit 직접 제공!)
- KRW 잔고 조회
- 거래 가능 마켓 목록

### Phase 2: 매도 주문 테스트 (XRP 5개)
- LIMIT 매도 주문 생성 (매도1호가 +100원, 절대 체결 안 됨) ✅
- 주문 조회 ✅
- 주문 취소 ✅
- MARKET 매도 (5 XRP 실제 체결!) 💰

### Phase 3: 매수 주문 테스트 (XRP 5개)
- LIMIT 매수 주문 생성 (매수1호가 -100원, 절대 체결 안 됨) ✅
- 주문 수정 (매수1호가 -200원으로 가격 하향, Cancel → Create) ✅
- 주문 취소 ✅
- MARKET 매수 (10,000 KRW 실제 체결!) 💰

### Phase 4: 최종 검증 ✅
- 미체결 주문 목록 확인
- 최종 보유량 확인
- 최종 KRW 잔고 확인

## Upbit 특징

### 장점
- **평단가 직접 제공**: `avg_buy_price` 필드로 평단가 계산 불필요
- **KRW 기반 거래**: 원화로 직관적인 거래

### 주의사항
- **주문 수정 API 없음**: Cancel → Create로 구현
- **시장가 주문 방식** ⚠️ 중요!:
  - **매수**: `ord_type="price"` + `price` (매수 **금액** KRW) ← SpotOrder.price에 금액 지정
  - **매도**: `ord_type="market"` + `volume` (매도 **수량** XRP) ← SpotOrder.quantity에 수량 지정
- **최소 주문 금액**: KRW 마켓은 5,000원 이상
- **LIMIT 주문 간격**: 테스트에서는 호가 ±100원으로 설정하여 즉시 체결 방지

## 사용 방법

### 1. API 키 설정

환경변수에 Upbit API 키를 설정합니다:

**Windows (PowerShell):**
```powershell
$env:UPBIT_ACCESS_KEY="your_access_key_here"
$env:UPBIT_SECRET_KEY="your_secret_key_here"
```

**Windows (CMD):**
```cmd
set UPBIT_ACCESS_KEY=your_access_key_here
set UPBIT_SECRET_KEY=your_secret_key_here
```

**Linux/Mac:**
```bash
export UPBIT_ACCESS_KEY="your_access_key_here"
export UPBIT_SECRET_KEY="your_secret_key_here"
```

### 2. 테스트 실행

```bash
cd C:\Projects\python-toolbox\packages\financial-gateway

# 전체 테스트 실행 (LIMIT + MARKET 모두 포함, 실제 거래 발생!)
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py -v -s

# Phase별 실행
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase1ReadOnly -v -s      # 읽기만
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase2SellOrders -v -s   # 매도 (LIMIT + MARKET)
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase3BuyOrders -v -s    # 매수 (LIMIT + MARKET)
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase4Verification -v -s # 최종 확인

# 개별 테스트 실행 예시
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase2SellOrders::test_13_market_sell_order -v -s
pytest tests/gateways/upbit_spot/test_upbit_spot_gateway.py::TestPhase3BuyOrders::test_23_market_buy_order -v -s
```

⚠️ **주의**: Phase 2/3에서 MARKET 주문이 실제로 체결됩니다!

## 테스트 시나리오

### 전체 테스트 흐름
```
[Phase 1: 읽기 전용]
초기: XRP, KRW 보유량 확인
↓
서버시간, 시세, 호가, 보유량, 잔고, 마켓 목록 조회
↓
[호가 기준 설정]
  매수1호가(best_bid): 1,350원 (예시)
  매도1호가(best_ask): 1,360원 (예시)
  스프레드: 10원
↓

[Phase 2: 매도 테스트]
LIMIT 매도: 5 XRP @ 1,460원 (매도1호가 +100원, 절대 체결 안 됨)
  → 주문 조회 → 주문 취소
↓
MARKET 매도: 5 XRP (quantity=5.0) 💰
  → 즉시 체결, ~6,750 KRW 획득 (수수료 차감)
↓

[Phase 3: 매수 테스트]
LIMIT 매수: 5 XRP @ 1,250원 (매수1호가 -100원, 절대 체결 안 됨)
  → 가격 수정 @ 1,150원 (매수1호가 -200원)
  → 주문 취소
↓
MARKET 매수: 10,000 KRW (price=10000) 💰
  → 즉시 체결, ~7.3 XRP 획득 (수수료 차감)
↓

[Phase 4: 최종 검증]
미체결 주문 확인 (모두 취소되었는지)
최종 XRP 보유량 확인
최종 KRW 잔고 확인
```

**예상 결과**: 5 XRP 매도 → 10,000 KRW로 매수 → 최종적으로 약 +2.3 XRP, -3,250 KRW (수수료 포함)

## API 키 권한 요구사항

- ✅ **자산 조회 권한** (View assets)
- ✅ **주문 생성/취소 권한** (Create/Cancel orders)
- ❌ 출금 권한 불필요

## Upbit vs Binance 차이점

| 항목 | Upbit | Binance |
|------|-------|---------|
| 기본 Quote | KRW | USDT |
| 평단가 | API 직접 제공 ✅ | Trade history 계산 필요 |
| 주문 수정 | Cancel → Create | cancelReplace API |
| 시장가 매수 | price (금액) | quantity (수량) |
| 최소 주문 | 5,000 KRW | 거래쌍별 상이 |

## 안전 수칙

1. **소량만 테스트**: 전체 보유량의 10% 미만 사용
2. **MARKET 주문 신중**: 기본적으로 스킵되어 있음
3. **최소 주문 금액**: KRW 마켓은 5,000원 이상
4. **에러 확인**: 모든 response.is_success 체크
5. **주문 정리**: 테스트 후 미체결 주문 확인 및 정리

## 문제 해결

### API 키가 설정되지 않음
```
SKIPPED - Upbit API keys not set
```
→ 환경변수 `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY` 설정 확인

### 인증 실패
```
AUTHENTICATION_FAILED
```
→ API 키 정확성 확인, IP 제한 확인

### 최소 주문 금액 미달
```
INVALID_QUANTITY or INVALID_PRICE
```
→ KRW 마켓은 5,000원 이상 주문 필요

### Rate Limit 초과
```
RATE_LIMIT_EXCEEDED
```
→ Upbit은 초당 제한이 엄격함:
- Quotation: 초당 10회
- Order: 초당 8회
- Non-Order: 초당 30회

## 추가 정보

- Upbit API 문서: https://docs.upbit.com/reference
- Upbit OpenAPI: https://docs.upbit.com/docs
