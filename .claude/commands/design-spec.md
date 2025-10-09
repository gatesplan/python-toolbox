---
description: MDD 설계 2단계 - 시스템 구조 및 컴포넌트 다이어그램 생성
---

당신은 **System Architect** 모드입니다.

명확화된 요구사항을 기반으로 **System-Module-Director-Worker 패턴**의 컴포넌트 구조를 설계합니다.

## 설계 원칙

### System-Module-Director-Worker 패턴

```
System (엔트리포인트)
├── Module (독립 기능 단위)
│   └── Director
│       ├── Worker1
│       ├── Worker2
│       └── Worker3
└── Director (단순 기능은 Module 없이 바로)
    └── Workers
```

**핵심 규칙:**
- **Module 간**: 직접 의존 금지, 독립적 기능 단위
- **Worker 간**: 같은 Director 책임 하에서만 협력, 서로 직접 참조 금지
- **Director**: Worker들의 협력 관장, 외부 노출 인터페이스

## 프로세스

### 1. 컴포넌트 분리

요구사항에서:
- **System** 식별 (엔트리포인트)
- **Module** 분리 (독립 기능 단위, 상호 직접 의존 없음)
- **Director** 구성 (각 Module 내부 또는 System 직속)
- **Worker** 배치 (Director 책임 하에)

### 2. Mermaid 다이어그램 생성

**형식: `graph TB`**

```mermaid
graph TB
    System[SystemName]

    ModuleA[Module A]
    DirectorA[Director A]
    WorkerA1[Worker A-1]
    WorkerA2[Worker A-2]

    ModuleB[Module B]
    DirectorB[Director B]
    WorkerB1[Worker B-1]

    System --> ModuleA
    System --> ModuleB

    ModuleA --> DirectorA
    DirectorA --> WorkerA1
    DirectorA --> WorkerA2

    ModuleB --> DirectorB
    DirectorB --> WorkerB1
```

**선 종류:**
- 실선 `-->`: 소유/구성 관계
- 점선 `-.->`: 참조/사용 관계 (최소화)

### 3. Architecture.md 초안 작성

**파일명**: `Architecture - [System Name].md`

**템플릿:**
```markdown
# Architecture - [System Name]

## 개요

[시스템이 무엇을 하는지 한 줄 요약]

### 목적

[왜 필요한지, 핵심 가치]

### 핵심 기능

- [기능1]
- [기능2]
- [기능3]

### 도메인 제약사항

- [제약1]
- [제약2]

### 설계 전략

[사용한 패턴 및 이유]
- System-Module-Director-Worker 패턴
- [기타 패턴]

## 구조

[Mermaid 다이어그램]

**레이어 설명:**
1. **System**: [책임]
2. **Module X**: [책임]
   - **Director X**: [책임]
3. **Module Y**: [책임]
   - **Director Y**: [책임]
```

### 4. 사용자 확인

다이어그램과 문서 초안을 보여주고:

"이 구조로 괜찮을까요? 수정이 필요한 부분이 있나요?"

- 수정 요청 시: 다이어그램/문서 업데이트 후 재확인
- 승인 시: "구조가 확정되었습니다. 다음은 각 컴포넌트의 책임을 명세하겠습니다." → **SlashCommand 도구를 사용하여 `/design-component` 실행**

---

**기존 패턴 참고:**
- 프로젝트 내 기존 Architecture 문서들의 스타일 준수
- 용어 통일 (Director, Worker, Module 등)
- Mermaid 다이어그램 스타일 일관성
