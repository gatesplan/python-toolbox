# Tasks: Simplify Docstring Style

## Sequence

### 1. Simplify CalculationTool docstrings
- [x] Update class docstring to 1-line Korean responsibility: "시뮬레이션 수치 계산 도구 (stateless 순수 함수)."
- [x] Simplify `round_to_min_amount` to Korean: "금액을 최소 거래 단위의 배수로 내림."
- [x] Simplify `get_price_sample` to Korean: "정규분포 기반 가격 샘플링 (범위 클리핑 적용)."
- [x] Simplify `get_separated_amount_sequence` to Korean: "금액을 랜덤하게 여러 조각으로 분할."
- [x] Simplify `get_price_range` to Korean: "target_price가 캔들의 어느 범위에 위치하는지 판단."
- [x] Remove all Args, Returns, Example sections
- [x] Run tests: `pytest tests/test_calculation_tool.py` - 16 passed

### 2. Simplify TradeFactory docstrings
- [x] Update class docstring to 2-3 line Korean responsibility (책임: ID 생성, Token 생성, 수수료 계산)
- [x] Simplify `create_spot_trade` to Korean: "단일 SpotTrade 생성 (수수료 자동 계산)."
- [x] Simplify `create_spot_trades_from_amounts` to Korean: "분할 수량으로 여러 Trade 생성 (각각 수수료 계산)."
- [x] Simplify `create_market_trades_with_slippage` to Korean: "시장가 주문용 - 각 Trade마다 다른 가격 및 수수료 계산."
- [x] Remove all Args, Returns, Example sections
- [x] Run tests: `pytest tests/test_trade_factory.py` - 4 passed

### 3. Simplify Worker docstrings
- [x] Simplify `SpotLimitWorker`: class to Korean 2-line (BUY/SELL 통합, 체결 조건), `__call__` to "지정가 주문 체결."
- [x] Simplify `SpotMarketBuyWorker`: class to Korean 2-line (항상 체결, head 슬리피지), `__call__` to "시장가 매수 체결."
- [x] Simplify `SpotMarketSellWorker`: class to Korean 2-line (항상 체결, tail 슬리피지), `__call__` to "시장가 매도 체결."
- [x] Remove all Args, Returns sections
- [x] Run tests: `pytest tests/test_spot_limit_buy_worker.py` - 4 passed

### 4. Simplify TradeSimulation docstrings
- [x] Update class docstring to Korean 2-3 lines (코어 클래스, order 라우팅 책임)
- [x] Simplify `__init__` to Korean: "TradeSimulation 초기화 - CalculationTool, TradeFactory와 워커 인스턴스 생성."
- [x] Simplify `process` to Korean: "Order를 처리하여 Trade 리스트 반환."
- [x] Simplify `_validate_process_param` to Korean: "파라미터 타입 검증."
- [x] Remove all Args, Returns, Raises sections
- [x] Run tests: `pytest tests/test_trade_simulation.py` - 4 passed

### 5. Final validation
- [x] Run full test suite: `pytest packages/financial-simulation/tests/` - 28 passed
- [x] Verify all tests pass (28 tests expected) - ✅ All passed
- [x] Review diff to confirm no logic changes - ✅ Only docstrings changed (83% reduction: 441 lines removed, 73 lines kept)
- [ ] Commit changes with descriptive message

## Dependencies
- No blocking dependencies
- Tasks 1-4 can run in parallel
- Task 5 must run after all modifications complete

## Validation
- All existing tests must pass
- No functional changes (git diff shows only docstring changes)
- Each modified file should reduce line count by 30-50%
