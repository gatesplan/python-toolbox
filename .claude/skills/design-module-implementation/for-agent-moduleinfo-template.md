# for-agent-moduleinfo.md Template

이 템플릿은 모듈 기술문서 작성을 위한 두 가지 형식을 제공합니다.

## 형식 1: 여러 모듈에 대해 설명하는 문서 (모듈 수준)

계층 루트에 위치하며, 여러 모듈의 목적과 책임만 간단히 설명합니다.
메서드의 상세 설명은 생략하고 시그니처만 제공합니다.

```
# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명

method(args: type, args: type = default) -> return_type
    raise ExceptionOrError
    메서드의 한 줄 설명

# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명

method(args: type, args: type = default) -> return_type
    raise ExceptionOrError
    메서드의 한 줄 설명

---

**사용 예시:**
```python
# 간단한 코드 예시 (선택 사항)
```
```

## 형식 2: 하나의 모듈에 대해 설명하는 문서 (클래스 수준)

각 서브모듈 폴더에 위치하며, 하나의 모듈을 상세히 설명합니다.
**메서드의 input/output 타입힌트와 동작을 명확히 정의합니다.**

```
# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명

## 섹션 제목 (선택 사항)

method(args: type, args: type = default) -> return_type
    메서드의 간단한 설명

    Args:
        args: 파라미터 설명
        args: 파라미터 설명 (default 값 명시)

    Returns:
        return_type: 반환값 설명

    Raises:
        ExceptionName: 예외 발생 조건 (선택 사항)

    Notes:
        - 추가 설명이나 주의사항 (선택 사항)
        - 특이한 동작이나 제약사항

---

**사용 예시:**
```python
# 실제 사용법을 보여주는 코드 예시
obj = ModuleName(arg1, arg2)
result = obj.method(param)
```

**의존성:**
- 의존하는 모듈 나열 (선택 사항)

**계산 로직:**
- 복잡한 계산이 있는 경우 설명 (선택 사항)
```

**구체적 예시:**
```
# PositionManager
포지션 조회 및 통계 제공. 총 자산 가치, 손익률, 포지션 비중 계산.

_portfolio: Portfolio       # Portfolio 인스턴스
_market_data: MarketData    # MarketData 인스턴스
_initial_balance: float     # 초기 자산 (손익률 계산용)

## 초기화

__init__(portfolio: Portfolio, market_data: MarketData, initial_balance: float) -> None
    PositionManager 초기화

    Args:
        portfolio: Portfolio 인스턴스
        market_data: MarketData 인스턴스 (현재 가격 조회용)
        initial_balance: 초기 자산 (손익률 계산 기준)

## 자산 가치 계산

get_total_value(quote_currency: str = "USDT") -> float
    총 자산 가치 계산 (Currency 잔고 + Position 현재 가치)

    Args:
        quote_currency: 기준 화폐 (기본값: "USDT")

    Returns:
        float: 총 자산 가치 (quote_currency 기준)

    Notes:
        - Currency 잔고는 현재 가격으로 환산
        - Position은 ticker에서 base/quote 추출하여 현재 가격으로 계산
        - 가격 데이터 없는 경우 0으로 처리

---

**사용 예시:**
```python
# 초기화
pm = PositionManager(portfolio, market_data, initial_balance=10000.0)

# 총 자산 가치
total = pm.get_total_value()  # 12345.67 USDT

# 손익률
pnl = pm.get_total_pnl()           # 2345.67 USDT
pnl_ratio = pm.get_total_pnl_ratio()  # 23.46%
```

**의존성:**
- Portfolio: 잔고 및 포지션 데이터 조회
- MarketData: 현재 가격 정보 조회 (get_current())

**계산 로직:**
- ticker 형식: "BASE-QUOTE" (예: "BTC-USDT")
- 가격 조회: market_data.get_current("BASE/QUOTE")
- Price 객체의 close 필드 사용
```

## 사용 가이드

**모듈 수준 (형식 1) 사용 시기:**
- API/, Service/, Core/ 같은 계층 루트에 작성
- 해당 계층의 모든 서브모듈 개요 제공
- 빠른 탐색 및 전체 구조 파악 목적
- 메서드 시그니처만 나열 (상세 설명 없음)

**클래스 수준 (형식 2) 사용 시기:**
- Service/PositionManager/ 같은 서브모듈 폴더에 작성
- 해당 모듈의 상세 API 및 사용법 제공
- 구체적 구현 가이드 목적
- **Args, Returns, Notes를 포함한 상세 설명**
- **사용 예시, 의존성, 계산 로직 등 추가 정보 제공**

**위치 예시:**
```
module/
├── Service/
│   ├── for-agent-moduleinfo.md           # 형식 1: 모든 Service 개요
│   ├── PositionManager/
│   │   ├── PositionManager.py
│   │   └── for-agent-moduleinfo.md       # 형식 2: 해당 Service 상세
│   └── OrderExecutor/
│       ├── OrderExecutor.py
│       └── for-agent-moduleinfo.md       # 형식 2: 해당 Service 상세
```

**작성 원칙:**
- 형식 1: 간결하게, 전체 구조 파악에 집중
- 형식 2: 상세하게, 구현에 필요한 모든 정보 제공
  - Args/Returns는 필수
  - Raises/Notes는 필요 시 추가
  - 사용 예시는 필수 (코드로 이해도 향상)
  - 의존성/계산 로직은 복잡한 경우 추가
