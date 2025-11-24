# 코딩 프로토콜 - 클래스 생성

이 문서는 코딩 에이전트가 클래스를 작성 시 지켜야 할 규칙과 작업 순서를 정의한다.


## 1. 전역 규칙

## 2. 클래스 작성 전 점검

### 2.1. 의존성 체크

- 의존성 순서 점검
- 불필요한 동적 임포트, 타입체킹 금지
- 임포트 순서 코드 prettify (일반적 원칙대로)

#### 예시
```python
# standard library
import os

# third party
from django.db import models
from __future__ import annotations

# second party
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderStatus

# local (in same package)
from ..Core import Portfolio, OrderBook, MarketData, OrderHistory, OrderRecord
from ..Service import OrderValidator, OrderExecutor, PositionManager, MarketDataService
from ...tradesim.API import TradeSimulation
```