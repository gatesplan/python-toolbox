# Design: Simplify Docstring Style for Financial-Assets

## Architectural Rationale

### Consistency with Financial-Simulation
financial-simulation 패키지에서 docstring 간소화를 성공적으로 완료했습니다:
- **83% 코드 감소**: 441줄 → 73줄
- **전체 테스트 통과**: 28/28 tests passed
- **에이전트 효율성 개선**: 토큰 소비 대폭 감소

financial-assets는 financial-simulation과 밀접하게 연동되므로, 동일한 docstring 스타일을 적용하여 일관성을 유지해야 합니다.

### Why Financial-Assets Needs Simplification

#### Current Problems
1. **스타일 불일치**: financial-simulation은 간결, financial-assets는 장황
2. **중복 정보**: Attributes 섹션이 타입 힌트와 100% 중복
3. **Example 코드**: 테스트 코드가 더 신뢰성 있는 예시 제공
4. **영어/한글 혼용**: 영어 클래스 docstring + 한글 메서드 docstring

#### Target Benefits
- **일관성**: 모든 패키지가 동일한 간결한 한글 스타일
- **토큰 효율**: 에이전트가 더 빠르게 코드 이해
- **유지보수**: 동기화할 docstring 줄어듦

## Design Principles (Same as Financial-Simulation)

### 1. Single Line of Intent
메서드는 **무엇을 하는가**만 설명합니다.

```python
# BAD: 너무 상세
def split_by_amount(self, amount: float) -> tuple[Token, Token]:
    """
    특정 금액으로 토큰을 분할합니다.

    splitted는 올림 처리되고, reduced는 원본에서 splitted를 뺀 값입니다.

    Args:
        amount: 분할할 금액

    Returns:
        (reduced, splitted): reduced는 남은 금액, splitted는 분할된 금액

    Raises:
        ValueError: amount가 음수이거나 원본보다 클 때

    Examples:
        >>> token = Token(symbol="BTC", amount=1.0)
        >>> reduced, splitted = token.split_by_amount(0.3)
    """

# GOOD: 의도만 전달
def split_by_amount(self, amount: float) -> tuple[Token, Token]:
    """특정 금액으로 토큰 분할."""
```

### 2. Type Hints Replace Attributes/Args/Returns
타입 힌트가 이미 완전한 정보를 제공합니다.

```python
# Type hints tell the full story
@dataclass(frozen=True)
class SpotTrade:
    """체결 완료된 현물 거래 (불변 데이터 구조)."""

    stock_address: StockAddress
    trade_id: str
    fill_id: str
    side: SpotSide
    pair: Pair
    timestamp: int
    fee: Optional[Token] = None
```

### 3. Class Docstring: Responsibility Only
클래스는 **책임 범위**만 설명합니다.

```python
# BAD: Attributes 나열
class SpotWallet:
    """
    단일 현물 거래 계정의 자산 및 거래 내역 관리.

    SpotWallet은 화폐 계정(USD, KRW 등)과 자산 포지션(BTC-USD, ETH-USD 등)을
    관리하며, 거래를 처리하고 내역을 자동으로 기록합니다.

    - 화폐 관리: 입금/출금, 잔액 조회
    - 거래 처리: BUY/SELL 거래 시 자산 조정 및 장부 기록
    - 포지션 관리: PairStack을 통한 평단가별 레이어 관리
    - 거래 기록: SpotLedger를 통한 자동 내역 기록

    Attributes:
        _currencies (dict[str, Token]): 화폐 계정
        _pair_stacks (dict[str, PairStack]): 자산 포지션
        _ledgers (dict[str, SpotLedger]): 거래 내역

    Examples:
        >>> wallet = SpotWallet()
        ...
    """

# GOOD: 책임만
class SpotWallet:
    """
    현물 거래 지갑.
    화폐 계정, 자산 포지션, 거래 내역을 관리하고 BUY/SELL 거래를 처리합니다.
    """
```

### 4. No Examples in Docstrings
테스트 코드가 더 신뢰성 있는 예시를 제공합니다.

```python
# GOOD: Example in test
def test_split_by_amount_basic(self):
    token = Token(symbol="BTC", amount=1.0)
    reduced, splitted = token.split_by_amount(0.3)
    assert reduced.amount == 0.7
    assert splitted.amount == 0.3
```

## File-by-File Strategy

### Priority 1: Core Data Structures (High Impact)
1. **Token**: 기본 단위, 모든 곳에서 사용
2. **Pair**: Token 조합, 거래 표현의 핵심
3. **PairStack**: Pair 컨테이너, Wallet에서 사용

### Priority 2: Order/Trade (Medium Impact)
4. **SpotOrder**: 주문 데이터, 시뮬레이션 입력
5. **SpotTrade**: 거래 결과, 시뮬레이션 출력
6. **SpotSide**: Enum, 간단

### Priority 3: Wallet/Ledger (Medium Impact)
7. **SpotLedger**: 거래 내역 저장
8. **SpotWallet**: 지갑 시뮬레이션 핵심
9. **WalletInspector**: 분석 도구

### Priority 4: Supporting (Low Impact)
10. **StockAddress**: 시장 정보
11. **Price**: 가격 정보

## Implementation Strategy

### Step-by-Step Approach
1. 각 파일을 독립적으로 수정 (병렬 작업 가능)
2. 수정 후 즉시 해당 파일의 테스트 실행
3. 모든 수정 완료 후 전체 테스트 실행
4. Git diff로 로직 변경 없음 확인

### Rollback Plan
- Git commit 단위로 작업하여 필요 시 revert 가능
- 테스트 실패 시 해당 파일만 rollback

## Trade-offs

### Gains
- **일관성**: financial-simulation과 동일한 스타일
- **토큰 효율성**: 에이전트가 더 빠르게 코드 이해
- **유지보수**: 동기화할 docstring 줄어듦
- **가독성**: 핵심 의도에 집중

### Costs
- **신규 개발자 온보딩**: 상세 설명 부족 (Architecture 문서로 보완)
- **API 문서 생성**: Sphinx 호환성 저하 (현재 미사용)

## Impact on Existing Systems
- **테스트**: 영향 없음 (docstring은 런타임 동작과 무관)
- **CI/CD**: 영향 없음
- **financial-simulation**: 긍정적 (스타일 일관성)
- **에이전트 워크플로우**: 긍정적 (더 빠른 이해)

## Future Considerations
- financial-indicators 패키지에도 동일 정책 적용 검토
- Candle storage 모듈 별도 작업 계획
- 프로젝트 전체 docstring 컨벤션 문서화 (`CLAUDE.md`에 추가)
