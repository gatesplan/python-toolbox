# BinanceSpotGateway 실거래 테스트

실제 Binance API를 사용하여 BinanceSpotGateway의 모든 기능을 테스트합니다.

## 테스트 구성

### Phase 1: 읽기 전용 (안전) ✅
- 서버 시간 조회
- XRP/USDT 시세 조회
- 호가창 조회
- XRP 보유량 및 평단가 조회
- USDT 잔고 조회

### Phase 2: 매도 주문 테스트
- LIMIT 매도 주문 생성 (현재가 +10%, 즉시 체결 안 됨) ✅
- 주문 조회 ✅
- 주문 취소 ✅
- MARKET 매도 (실제 체결!) ⚠️ **기본 스킵**

### Phase 3: 매수 주문 테스트
- LIMIT 매수 주문 생성 (현재가 -10%, 즉시 체결 안 됨) ✅
- 주문 수정 (가격 변경) ✅
- 주문 취소 ✅
- MARKET 매수 (실제 체결!) ⚠️ **기본 스킵**

### Phase 4: 최종 검증 ✅
- 미체결 주문 목록 확인
- 최종 XRP 보유량 확인
- 최종 USDT 잔고 확인

## 사용 방법

### 1. API 키 설정

환경변수에 Binance API 키를 설정합니다:

**Windows (PowerShell):**
```powershell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

**Windows (CMD):**
```cmd
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

**Linux/Mac:**
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

### 2. 안전한 테스트 실행 (실제 체결 없음)

```bash
cd C:\Projects\python-toolbox\packages\financial-gateway

# Phase 1만 실행 (읽기 전용)
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase1ReadOnly -v -s

# Phase 1~3 실행 (LIMIT 주문만, 모두 취소)
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase1ReadOnly -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase2SellOrders::test_10_create_limit_sell_order -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase2SellOrders::test_11_query_sell_order -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase2SellOrders::test_12_cancel_sell_order -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase3BuyOrders::test_20_create_limit_buy_order -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase3BuyOrders::test_21_modify_buy_order -v -s
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase3BuyOrders::test_22_cancel_buy_order -v -s

# Phase 4 실행 (최종 확인)
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase4Verification -v -s
```

### 3. 실제 체결 테스트 (주의!)

⚠️ **실제로 XRP가 매도/매수됩니다!**

테스트 파일을 수정하여 MARKET 주문 스킵을 해제합니다:

```python
# test_binance_spot_gateway.py 244번째 줄
@pytest.mark.skipif(False, reason="실제 체결 활성화")  # True → False로 변경
async def test_13_market_sell_order(self, gateway, xrp_usdt_address):
    ...

# test_binance_spot_gateway.py 371번째 줄
@pytest.mark.skipif(False, reason="실제 체결 활성화")  # True → False로 변경
async def test_23_market_buy_order(self, gateway, xrp_usdt_address):
    ...
```

그리고 실행:

```bash
# Phase 2 MARKET 매도 (2 XRP 매도)
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase2SellOrders::test_13_market_sell_order -v -s

# Phase 3 MARKET 매수 (1.9 XRP 매수)
pytest tests/gateways/binance_spot/test_binance_spot_gateway.py::TestPhase3BuyOrders::test_23_market_buy_order -v -s
```

## 테스트 시나리오

### 안전한 테스트 (기본)
```
초기: XRP 49개
↓
[읽기 테스트] 시세, 호가, 보유량 조회
↓
[LIMIT 매도] 3 XRP @ 현재가+10% (생성 → 조회 → 취소)
↓
[LIMIT 매수] 2 XRP @ 현재가-10% (생성 → 수정 → 취소)
↓
최종: XRP 49개 (변동 없음)
```

### 전체 사이클 (실제 체결)
```
초기: XRP 49개
↓
[LIMIT 매도] 3 XRP (취소)
↓
[MARKET 매도] 2 XRP → ~5 USDT 획득
↓
[LIMIT 매수] 2 XRP (취소)
↓
[MARKET 매수] 1.9 XRP ← ~4.8 USDT 사용
↓
최종: XRP ~48.9개, USDT ~0.2개
(수수료로 약 0.1 XRP 손실)
```

## API 키 권한 요구사항

- ✅ **읽기 권한** (Enable Reading)
- ✅ **스팟 거래 권한** (Enable Spot & Margin Trading)
- ❌ 출금 권한 불필요

## 안전 수칙

1. **테스트넷 사용 권장**: 먼저 Binance Testnet에서 테스트
2. **소량만 테스트**: 전체 보유량의 10% 미만 사용
3. **MARKET 주문 신중**: 기본적으로 스킵되어 있음
4. **에러 확인**: 모든 response.is_success 체크
5. **주문 정리**: 테스트 후 미체결 주문 확인 및 정리

## 문제 해결

### API 키가 설정되지 않음
```
SKIPPED - Binance API keys not set
```
→ 환경변수 `BINANCE_API_KEY`, `BINANCE_API_SECRET` 설정 확인

### 인증 실패
```
AUTHENTICATION_FAILED
```
→ API 키 정확성 확인, IP 화이트리스트 확인

### Rate Limit 초과
```
RATE_LIMIT_EXCEEDED
```
→ 테스트 간 대기 시간 추가, throttler 설정 확인

### 수량/가격 에러
```
INVALID_QUANTITY or INVALID_PRICE
```
→ Binance의 최소 주문 수량/가격 제한 확인 (exchangeInfo)

## 추가 정보

- Binance API 문서: https://binance-docs.github.io/apidocs/spot/en/
- Binance Testnet: https://testnet.binance.vision/
