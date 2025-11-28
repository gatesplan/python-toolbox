# Core Functions

순수 계산 함수 모음. 기술 지표 계산의 기본 빌딩 블록 제공.

## 특징

- **Stateless**: 모든 함수는 순수 함수, 부수효과 없음
- **독립적**: 대부분 함수는 다른 함수에 의존하지 않음
- **재사용 가능**: 어떤 컨텍스트에서도 사용 가능
- **NaN 패딩**: 출력 길이는 항상 입력과 동일, 계산 불가 영역은 NaN

## 하위 모듈

### rolling/
롤링 윈도우 기반 연산. 시계열 데이터의 이동 통계량 계산.

- **sma**: 단순이동평균 (Simple Moving Average)
- **ema**: 지수이동평균 (Exponential Moving Average)
- **wma**: 가중이동평균 (Weighted Moving Average)
- **std**: 롤링 표준편차 (Rolling Standard Deviation)
- **max**: 롤링 최댓값 (Rolling Maximum)
- **min**: 롤링 최솟값 (Rolling Minimum)
- **zscore**: 롤링 Z-Score (표준화 점수)

**의존성:**
- zscore → sma, std

### series/
시계열 변환 연산. 데이터 정규화, 변화율, 교차 탐지.

- **scaling**: Min-Max 스케일링
- **standardize**: 표준화 (Z-Score Normalization)
- **pct_change**: 퍼센트 변화율
- **log_return**: 로그 수익률
- **diff**: 차분 (Difference)
- **crossover**: 교차 탐지 (Golden/Death Cross)
- **shift**: 배열 이동

**의존성:**
- 모든 함수 독립적

---

**사용 패턴:**
```python
# 개별 함수 import
from financial_indicators.core.rolling import sma, ema
from financial_indicators.core.series import pct_change

# 계산
prices = np.array([100, 102, 101, 103, 105])
sma_3 = sma(prices, window=3)
pct = pct_change(prices, periods=1)
```

**설계 원칙:**
- 각 함수는 단일 파일로 분리 (모듈화)
- 타입 힌트 명확히 제공
- 예외 조건 명시 (ValueError)
- 엣지 케이스 처리 (0 나누기, 빈 배열 등)
