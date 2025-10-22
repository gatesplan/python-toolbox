# Spec: CalculationTool

## Overview

시뮬레이션에 필요한 수치 계산 유틸리티를 제공하는 도구 클래스입니다.

## ADDED Requirements

### Requirement: CalculationTool MUST provide minimum amount rounding

CalculationTool MUST provide a function to round down amounts to multiples of the minimum trade unit.

#### Scenario: Round amount to minimum trade unit

**Given** amount가 1.234이고 min_amount가 0.01일 때
**When** `round_to_min_amount(1.234, 0.01)`을 호출하면
**Then** 1.23을 반환해야 합니다

**Given** amount가 10.567이고 min_amount가 0.1일 때
**When** `round_to_min_amount(10.567, 0.1)`을 호출하면
**Then** 10.5를 반환해야 합니다

**Given** amount가 5.0이고 min_amount가 1.0일 때
**When** `round_to_min_amount(5.0, 1.0)`을 호출하면
**Then** 5.0을 반환해야 합니다

#### Scenario: Handle edge cases for rounding

**Given** amount가 0이고 min_amount가 0.01일 때
**When** `round_to_min_amount(0, 0.01)`을 호출하면
**Then** 0.0을 반환해야 합니다

**Given** amount가 0.001이고 min_amount가 0.01일 때
**When** `round_to_min_amount(0.001, 0.01)`을 호출하면
**Then** 0.0을 반환해야 합니다 (최소 단위보다 작으면 0)

### Requirement: CalculationTool MUST provide price sampling from normal distribution

CalculationTool MUST provide a function to sample prices within a given range using normal distribution.

#### Scenario: Sample price within range using normal distribution

**Given** 가격 범위가 [100, 110]이고 평균이 105, 표준편차가 2일 때
**When** `get_price_sample(100, 110, 105, 2)`를 호출하면
**Then** 100 이상 110 이하의 가격을 반환해야 합니다

**Given** z-score 범위가 [-2, 2]로 제한될 때
**When** 정규분포에서 샘플링하면
**Then** 결과는 mean ± 2*std 범위 내에 있어야 합니다

#### Scenario: Clip sampled price to min-max bounds

**Given** 가격 범위가 [100, 102]이고 평균이 105, 표준편차가 5일 때
**When** `get_price_sample(100, 102, 105, 5)`를 호출하면
**Then** 정규분포 샘플이 범위를 벗어나더라도 100 이상 102 이하 값을 반환해야 합니다

### Requirement: CalculationTool MUST provide amount separation into random pieces

CalculationTool MUST provide a function to randomly split an amount into a specified number of pieces while respecting minimum trade unit constraints.

#### Scenario: Separate amount into multiple pieces

**Given** base가 10.0이고 min_trade_amount가 0.1이고 split_to가 3일 때
**When** `get_separated_amount_sequence(10.0, 0.1, 3)`을 호출하면
**Then** 3개의 float 리스트를 반환해야 합니다
**And** 각 요소는 0.1의 배수여야 합니다
**And** 모든 요소의 합은 10.0이어야 합니다

#### Scenario: Each piece respects minimum trade amount

**Given** base가 5.0이고 min_trade_amount가 1.0이고 split_to가 2일 때
**When** `get_separated_amount_sequence(5.0, 1.0, 2)`을 호출하면
**Then** 각 조각은 1.0 이상이어야 합니다 (최소 거래 단위)
**And** 각 조각은 1.0의 배수여야 합니다

#### Scenario: Handle rounding remainder in last piece

**Given** base가 10.0이고 min_trade_amount가 0.3이고 split_to가 3일 때
**When** `get_separated_amount_sequence(10.0, 0.3, 3)`을 호출하면
**Then** 각 조각을 0.3 배수로 내림한 후 남은 잔여량은 마지막 조각에 추가되어야 합니다
**And** 모든 조각의 합은 정확히 10.0이어야 합니다

#### Scenario: Single piece returns base amount

**Given** base가 7.5이고 min_trade_amount가 0.1이고 split_to가 1일 때
**When** `get_separated_amount_sequence(7.5, 0.1, 1)`을 호출하면
**Then** [7.5]를 반환해야 합니다

### Requirement: CalculationTool methods MUST be stateless and pure

All methods of CalculationTool MUST be stateless and pure, producing identical outputs for identical inputs when random seed is fixed.

#### Scenario: Methods have no side effects

**Given** CalculationTool 인스턴스가 있을 때
**When** 임의의 메서드를 호출하면
**Then** 인스턴스 상태가 변경되지 않아야 합니다
**And** 글로벌 상태가 변경되지 않아야 합니다

#### Scenario: Reproducible with random seed

**Given** numpy random seed를 42로 설정했을 때
**When** `get_separated_amount_sequence(10.0, 0.1, 3)`을 두 번 호출하면
**Then** 두 결과가 동일해야 합니다
