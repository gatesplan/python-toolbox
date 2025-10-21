# Design: Refactor SpotOrder to Simplify Responsibility

## Context
현재 `SpotOrder` 클래스는 주문 정보를 표현하는 동시에 거래 처리 로직(`fill_by_*` 메서드를 통한 SpotTrade 생성)까지 담당하고 있습니다. 이는 단일 책임 원칙(SRP)을 위반하며, Order가 Trade에 강하게 결합되어 있습니다.

사용자 피드백:
- `filled_amount` 필드가 Order에 있다는 것은 "얼마나 체결되었는지" 추적하는 것이 Order의 책임
- `fill` 메서드 자체는 목적에 맞지만, SpotTrade 생성까지 하는 것은 과함
- Order는 순수한 데이터 표현 + 불변 업데이트 편의 메서드를 제공하는 것이 적절

## Goals / Non-Goals

### Goals
- SpotOrder를 순수한 데이터 클래스로 유지하되, 불변 업데이트 편의 메서드 제공
- SpotTrade 생성 로직을 외부로 분리
- 불변 복제 패턴을 통해 예측 가능하고 안전한 상태 관리
- `filled_amount`와 `status` 필드는 유지하되, 업데이트는 불변 방식으로

### Non-Goals
- Order를 완전히 immutable frozen dataclass로 만들기 (편의성 저하)
- 거래 처리 시스템(OrderFiller, OrderExecutor) 구현 (별도 작업)
- split 기능 제공 (불필요 - 외부에서 새 Order 생성으로 충분)

## Decisions

### 1. fill 메서드: SpotTrade 반환 제거, SpotOrder 반환
- **결정**: `fill_by_asset_amount()`, `fill_by_value_amount()` 메서드는 유지하되, SpotTrade 생성 로직 제거
  - 기존: `fill_by_asset_amount(amount, price, timestamp) -> SpotTrade`
  - 변경: `fill_by_asset_amount(amount) -> SpotOrder`
- **이유**:
  - filled_amount 업데이트는 Order의 정당한 책임
  - SpotTrade 생성은 외부에서 처리하는 것이 책임 분리에 적합
  - 불변 복제 패턴으로 원본 보존 + 업데이트된 새 인스턴스 반환
- **불변 복제 패턴**:
  ```python
  def fill_by_asset_amount(self, amount: float) -> SpotOrder:
      # 유효성 검사
      self._validate_fill(amount)

      # 새 filled_amount 계산
      new_filled = self.filled_amount + amount

      # 상태 자동 판단
      if new_filled >= self.amount:
          new_status = "filled"
      elif new_filled > 0:
          new_status = "partial"
      else:
          new_status = "pending"

      # 새 인스턴스 생성 (모든 필드 복제)
      return SpotOrder(
          order_id=self.order_id,
          stock_address=self.stock_address,
          side=self.side,
          order_type=self.order_type,
          price=self.price,
          amount=self.amount,
          timestamp=self.timestamp,
          stop_price=self.stop_price,
          filled_amount=new_filled,
          status=new_status
      )
  ```

### 2. 상태 변경 메서드: to_*_state() 패턴
- **결정**: `to_pending_state()`, `to_partial_state()`, `to_filled_state()`, `to_canceled_state()` 추가
- **이유**:
  - 명시적 상태 변경 필요 시 사용 (예: 주문 취소)
  - 불변 복제 패턴 일관성 유지
  - `to_*` prefix로 "새로운 것으로 변환"의 의미 명확화
- **대안 고려**:
  - `make_*()`: 덜 명확한 의미
  - `with_status(status)`: 일반화되어 있지만 타입 안정성 떨어짐
  - `cancel()`: 가변 방식이라 불변 패턴과 불일치

### 3. cancel() 메서드 제거
- **결정**: 기존 `cancel()` 메서드 제거, `to_canceled_state()`로 대체
- **이유**:
  - 불변 복제 패턴과의 일관성
  - 명시적으로 새 인스턴스 반환을 표현

### 4. __init__에 filled_amount, status, fee_rate 추가
- **결정**: `__init__` 시그니처에 `filled_amount=0.0`, `status="pending"`, `fee_rate=0.0` 파라미터 추가
- **이유**:
  - 불변 복제 시 모든 필드를 명시적으로 전달 가능
  - 외부에서도 특정 상태의 Order 인스턴스를 직접 생성 가능
  - `fee_rate`: 거래 처리에 필요한 수수료 정보를 Order가 포함하여 stateless 처리 가능

### 5. fee_rate 필드 추가
- **결정**: `fee_rate: float = 0.0` 필드 추가하여 수수료 비율 저장
- **이유**:
  - Order가 거래 처리에 필요한 모든 정보를 포함해야 stateless 처리 가능
  - 거래소마다 다른 fee 정책을 Order 단위로 관리 가능
  - 외부에서 SpotTrade 생성 시 `order.fee_rate`를 사용해 Token 타입의 fee 계산
  - 간단한 비율(float)로 저장하여 Order를 단순하게 유지
- **대안 고려**:
  - `maker_fee_rate + taker_fee_rate` 구분: 과도하게 복잡, 필요시 나중에 추가 가능
  - Token 타입으로 fee 저장: Order의 책임이 과도하게 증가, 외부에서 계산하는 것이 적절
- **fee 계산 예시**:
  ```python
  # BUY 주문: quote 통화로 수수료 납부
  fee_amount = fill_amount * fill_price * order.fee_rate
  fee = Token(symbol=order.stock_address.quote, amount=fee_amount)

  # SELL 주문: base 통화로 수수료 납부
  fee_amount = fill_amount * order.fee_rate
  fee = Token(symbol=order.stock_address.base, amount=fee_amount)
  ```

### 6. split 기능 불필요
- **결정**: split_by_asset_amount(), split_by_value_amount() 메서드를 추가하지 않음
- **이유**:
  - 외부에서 `SpotOrder(order_id="...", amount=0.3, ...)` 식으로 새 인스턴스 생성하면 됨
  - 편의 메서드로서의 가치가 낮음
  - Token과 달리 정밀도 조정이나 복잡한 분할 로직이 필요 없음

## Risks / Trade-offs

### Risk: Breaking Change
- **리스크**: 기존 fill 메서드의 반환 타입이 변경됨 (SpotTrade → SpotOrder)
- **완화 전략**:
  - 명확한 마이그레이션 가이드 제공
  - 외부에서 SpotTrade 생성하는 예제 코드 제공
  - 테스트 코드 먼저 업데이트하여 예시로 활용

### Trade-off: 불변성 vs 성능
- **트레이드오프**: 매번 새 인스턴스 생성으로 메모리 오버헤드 발생
- **판단**: Order 객체는 크지 않고, 거래 빈도가 극단적으로 높지 않아 무시 가능한 수준

### Trade-off: 명시적 복제 vs 간결함
- **트레이드오프**: 불변 패턴으로 코드가 길어질 수 있음
  ```python
  # 가변 방식 (기존)
  order.fill_by_asset_amount(0.3, 50000, 123456)
  wallet.process_trade(order.last_trade)

  # 불변 방식 (변경 후)
  updated_order = order.fill_by_asset_amount(0.3)
  trade = SpotTrade(...)  # 외부에서 생성
  wallet.process_trade(trade)
  ```
- **판단**: 명시성과 안전성이 더 중요. 외부 거래 처리 시스템에서 래핑하면 간결함 회복 가능

## Migration Plan

### 단계 1: SpotOrder 리팩토링
1. `__init__`에 `filled_amount`, `status`, `fee_rate` 파라미터 추가
2. `fill_by_asset_amount()` 수정: SpotTrade 생성 제거, SpotOrder 반환
3. `fill_by_value_amount()` 수정: 동일하게 변경
4. `to_pending_state()`, `to_partial_state()`, `to_filled_state()`, `to_canceled_state()` 추가
5. `cancel()` 메서드 제거
6. `_validate_fill()` 유지 (검증 로직 필요)

### 단계 2: 테스트 업데이트
1. fill 메서드 테스트를 SpotOrder 반환 기준으로 수정
2. 불변성 테스트 추가 (원본 변경되지 않음 검증)
3. 상태 변경 메서드 테스트 추가
4. SpotTrade 생성 로직은 별도 테스트로 분리

### 단계 3: 문서화
1. docstring 업데이트: SpotTrade 반환 언급 제거
2. 사용 예제를 불변 복제 패턴으로 변경
3. 외부에서 SpotTrade 생성하는 예제 추가

### Rollback 계획
- 변경 사항이 문제 발생 시 이전 커밋으로 완전히 되돌림
- **레거시 호환성 유지하지 않음**: 기존 코드는 반드시 수정 필요

## Implementation Notes

### 불변 복제 헬퍼 메서드
모든 필드를 복제하는 로직이 반복되므로, 내부 헬퍼 메서드 고려:

```python
def _clone(self, **overrides) -> SpotOrder:
    """내부 헬퍼: 모든 필드 복제 + 일부 오버라이드"""
    return SpotOrder(
        order_id=overrides.get('order_id', self.order_id),
        stock_address=overrides.get('stock_address', self.stock_address),
        side=overrides.get('side', self.side),
        order_type=overrides.get('order_type', self.order_type),
        price=overrides.get('price', self.price),
        amount=overrides.get('amount', self.amount),
        timestamp=overrides.get('timestamp', self.timestamp),
        stop_price=overrides.get('stop_price', self.stop_price),
        filled_amount=overrides.get('filled_amount', self.filled_amount),
        status=overrides.get('status', self.status),
        fee_rate=overrides.get('fee_rate', self.fee_rate)
    )

def fill_by_asset_amount(self, amount: float) -> SpotOrder:
    self._validate_fill(amount)
    new_filled = self.filled_amount + amount
    new_status = "filled" if new_filled >= self.amount else "partial"
    return self._clone(filled_amount=new_filled, status=new_status)

def to_canceled_state(self) -> SpotOrder:
    return self._clone(status="canceled")
```

### 상태 자동 판단 로직
- `fill_by_*` 메서드는 자동으로 status 결정
- `filled_amount >= amount`이면 "filled", 그 외 "partial"
- 0이면 "pending" 유지

## Open Questions
1. **Q**: `dataclasses.replace()` 또는 `copy.copy()` 사용 고려?
   - **A**: 명시적 생성자 호출이 더 명확하고, 향후 검증 로직 추가 시 유리

2. **Q**: `to_*_state()` 메서드들이 filled_amount를 리셋해야 하나요?
   - **A**: 아니요. 상태만 변경하고 다른 필드는 유지합니다.

3. **Q**: 외부에서 SpotTrade를 어떻게 생성하나요?
   - **A**:
   ```python
   updated_order = order.fill_by_asset_amount(0.3)

   # fee 계산 (BUY는 quote 통화로 수수료)
   fill_price = 50100.0
   fill_amount = 0.3
   fee_amount = fill_amount * fill_price * order.fee_rate

   trade = SpotTrade(
       stock_address=order.stock_address,
       trade_id=order.order_id,
       side=order.side,
       pair=Pair(
           asset=Token(order.stock_address.base, fill_amount),
           value=Token(order.stock_address.quote, fill_amount * fill_price)
       ),
       timestamp=fill_timestamp,
       fee=Token(order.stock_address.quote, fee_amount) if order.fee_rate > 0 else None
   )
   ```

4. **Q**: fee 계산 시 BUY/SELL 구분은 어떻게 하나요?
   - **A**: 일반적으로 BUY는 quote 통화로, SELL은 base 통화로 수수료 납부합니다:
   ```python
   if order.side == SpotSide.BUY:
       fee = Token(order.stock_address.quote, fill_amount * fill_price * order.fee_rate)
   else:  # SELL
       fee = Token(order.stock_address.base, fill_amount * order.fee_rate)
   ```
