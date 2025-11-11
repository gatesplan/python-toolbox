# for-agent-moduleinfo.md Template

이 템플릿은 모듈 기술문서 작성을 위한 두 가지 형식을 제공합니다.

## 형식 1: 여러 모듈에 대해 설명하는 문서 (모듈 수준)

계층 루트에 위치하며, 여러 모듈의 목적과 책임만 간단히 설명합니다.
메서드를 일일이 나열하지 않습니다.

```
# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명
method(args: type, args: type = default) -> return_type
    raise ExceptionOrError
    메서드의 간단한 설명

# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명
method(args: type, args: type = default) -> return_type
    raise ExceptionOrError
    메서드의 간단한 설명

...
```

## 형식 2: 하나의 모듈에 대해 설명하는 문서 (클래스 수준)

각 서브모듈 폴더에 위치하며, 하나의 모듈을 상세히 설명합니다.
**메서드의 input/output 타입힌트를 명확히 정의합니다.**

```
# modulename
모듈의 목적과 책임범위에 대한 간단한 설명

property: type = default    # 간단한 설명
property: type = default    # 간단한 설명

method(args: type, args: type = default) -> return_type
    raise ExceptionOrError
    메서드의 간단한 설명

    Args:
        args: 파라미터 설명
        args: 파라미터 설명 (default 값 명시)

    Returns:
        return_type: 반환값 설명

...
```

**구체적 예시:**
```
# SpotLimitFillService
지정가 주문 체결 시뮬레이션 서비스

_order: SpotOrder    # 처리 중인 주문
_price: Price        # 현재 가격 데이터

execute(order: SpotOrder, price: Price) -> List[TradeParams]
    주문과 현재 가격을 기반으로 체결 파라미터 리스트 생성

    Args:
        order: 처리할 지정가 주문 (SpotOrder 타입)
        price: 현재 시장 가격 (OHLC 데이터 포함)

    Returns:
        List[TradeParams]: 체결 파라미터 리스트. 체결 실패 시 빈 리스트 반환
```

## 사용 가이드

**모듈 수준 (형식 1) 사용 시기:**
- API/, Service/, Core/ 같은 계층 루트에 작성
- 해당 계층의 모든 서브모듈 개요 제공
- 빠른 탐색 및 전체 구조 파악 목적

**클래스 수준 (형식 2) 사용 시기:**
- Service/SpotLimitFillService/ 같은 서브모듈 폴더에 작성
- 해당 모듈의 상세 API 및 사용법 제공
- 구체적 구현 가이드 목적

**위치 예시:**
```
module/
├── Service/
│   ├── for-agent-moduleinfo.md           # 형식 1: 모든 Service 개요
│   ├── SpotLimitFillService/
│   │   ├── SpotLimitFillService.py
│   │   └── for-agent-moduleinfo.md       # 형식 2: 해당 Service 상세
│   └── SpotMarketBuyFillService/
│       ├── SpotMarketBuyFillService.py
│       └── for-agent-moduleinfo.md       # 형식 2: 해당 Service 상세
```
