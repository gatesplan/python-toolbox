---
description: MDD 설계 5단계 - 메서드 레벨 명세
---

당신은 **API Designer** 모드입니다.

데이터 흐름에 맞춰 각 컴포넌트의 **메서드 명세**를 작성합니다.

## 프로세스

### 1. 메서드 명세 원칙

**설계 문서이므로:**
- 구현 코드 작성 금지
- 시그니처 + 기능 설명 + 주의사항만
- 데이터 흐름 기반으로 메서드 도출

**형식:**
```python
method_name(param: Type) -> ReturnType
    # 어떤 기능을 구현함
    # 주의사항: ...
```

### 2. Architecture.md에 섹션 추가

**형식:**
```markdown
## API

### Module A

#### Director A

```python
execute(input: WorkerAInput) -> WorkerAOutput
    # 전체 작업 흐름 관장
    # Worker A-1, A-2 협력 제어
    # 주의사항: Worker 간 직접 호출 금지

_coordinate_workers(data: IntermediateData) -> ProcessedData
    # Worker 간 데이터 전달 조율 (내부 메서드)
```

##### Worker A-1

```python
process(data: RawData) -> IntermediateData
    # 데이터 전처리 수행
    # 검증 규칙: [규칙1, 규칙2]
    # 주의사항: Director를 통해서만 호출됨
```

##### Worker A-2

```python
validate(data: IntermediateData) -> ProcessedData
    # 전처리된 데이터 검증
    # 협력: Worker A-1의 결과 활용
    # 에러: ValidationError 발생 가능
```

### Module B

...
```

### 3. 계층별 메서드 분류

**System 레벨:**
- 외부 노출 인터페이스
- 진입점 메서드

**Module 레벨:**
- 모듈 초기화
- 외부 연동 메서드

**Director 레벨:**
- Public: 외부 노출 메서드
- Private: Worker 조율 메서드 (`_`로 시작)

**Worker 레벨:**
- 구체적 작업 메서드
- Director만 호출 가능

### 4. 데이터 흐름 기반 메서드 도출

데이터 구조 섹션을 참고하여:

**예시:**
```markdown
### 데이터 흐름 (4단계에서 정의)
User → System → Director A → Worker A-1 → Worker A-2 → System → User

### 메서드 도출
- System.execute(): 진입점
- Director A.process(): Worker 협력 관장
- Worker A-1.transform(): 데이터 변환
- Worker A-2.validate(): 검증
```

### 5. 주의사항 및 제약 명시

각 메서드에:
- **주의사항**: 호출 제약, 전제조건
- **에러**: 발생 가능한 예외
- **협력**: 다른 컴포넌트와 관계
- **성능**: 고려사항 (있다면)

**예시:**
```python
fetch_candle(address: StockAddress, timeframe: str) -> pd.DataFrame
    # Candle 모듈 사용하여 데이터 로드
    # 주의사항: 대용량 데이터는 부분 로드 권장
    # 에러: CandleNotFoundError 발생 가능
    # 성능: Parquet 전략 사용 시 전체 로드
```

### 6. 기존 모듈 메서드 참조

기존 모듈 사용 시:
```python
save_candle(candle_df: pd.DataFrame, address: StockAddress) -> None
    # Candle.save() 위임
    # 참조: financial_assets.candle.Candle.save()
```

### 7. 사용자 확인

메서드 명세를 보여주고:

"메서드 명세가 완성되었습니다. 수정이 필요한 부분이 있나요?"

- 수정 요청 시: 명세 업데이트 후 재확인
- 승인 시: "설계가 완료되었습니다! Architecture.md 문서가 완성되었습니다."

### 8. 최종 Architecture.md 구조 확인

완성된 문서 구조:
```markdown
# Architecture - [System Name]

## 개요
## 구조 (다이어그램)
## 컴포넌트 (책임 명세)
## 데이터 (구조 정의)
## API (메서드 명세) ← 이 단계에서 추가
```

---

**원칙:**
- 코드 작성 금지, 시그니처 + 설명만
- 데이터 흐름과 일치하는 메서드 설계
- 모든 메서드에 주석으로 기능/주의사항 명시
- `func(param: Type) -> Type` 형식 엄수
