---
name: design-system-architecture
description: 시스템 설계를 요청시 사용. 시스템 요구사항을 분석하여 필요한 모듈/컴포넌트를 식별하고 Architecture - *.md 문서를 작성. 전체 시스템의 컴포넌트 구조와 관계를 정의한다.
version: 1.0.0
---

# Design System Architecture

사용자의 요구사항을 분석하여 시스템에 필요한 모듈/컴포넌트를 식별하고, 이들의 관계를 정의하는 Architecture - *.md 문서를 작성한다.

## 작업 목표

**1단계: 시스템 레벨 설계**
- 전체 시스템 요구사항 분석
- 필요한 도메인/모듈 식별
- **컴포넌트 임명**: "이런 역할을 하는 컴포넌트가 필요하다"
- 컴포넌트 간 관계 및 의존성 정의
- Mermaid 다이어그램으로 시각화

**작업 범위:**
- ✓ 컴포넌트 식별 및 역할 정의
- ✓ 컴포넌트 간 의존성 관계
- ✗ 구체적 패턴 선택 (2단계: design-module-implementation)
- ✗ API 명세, 데이터 구조 (2단계)
- ✗ 디렉토리 구조 (2단계)

## 작업 프로세스

### 1. 요구사항 분석
- 사용자의 요구사항에서 핵심 기능 추출
- 도메인 개념 식별
- 필요한 모듈/컴포넌트 후보 나열

### 2. 컴포넌트 임명
- 각 도메인/기능을 담당할 컴포넌트 정의
- 컴포넌트의 **고수준 책임** 명시
- 컴포넌트 이름 결정

**예시:**
```
요구사항: "거래 체결 시뮬레이션"
→ 컴포넌트:
  - TradeSimulation: 전체 체결 시뮬레이션 흐름 관장
  - FillService: 체결 로직 수행
  - CandleAnalyzer: 캔들 데이터 분석
  - TradeFactory: Trade 객체 생성
```

### 3. 관계 정의
- 컴포넌트 간 의존성 방향
- 데이터 흐름
- 호출 관계

### 4. 다이어그램 작성
- Mermaid graph로 컴포넌트 관계 시각화
- 각 노드에 역할 간략히 표시
- 의존성 화살표로 관계 표현

### 5. 문서 작성
- `architecture-template.md` 참조
- Overview, Core Features, Structure 섹션 작성
- **구체적 구현 내용은 포함하지 않음**

## 출력물

**Architecture - {ModuleName}.md**
- Overview: 모듈 목적 및 핵심 개념
- Core Features: 주요 기능 목록
- Design Philosophy: (선택) 설계 철학
- Dependencies: 외부 패키지 의존성
- Structure: Mermaid 다이어그램 + 컴포넌트 책임

## Followup Guide

- 설계에 있어 판단이 필요한 불분명한 사항이 있을 시: 사용자의 의견을 확인한다.
- Architecture 문서 작성 후: 사용자에게 "구체적인 모듈 구현 설계가 필요하면 design-module-implementation 스킬을 사용하세요"라고 안내한다.
- 기존 시스템에 새 모듈 추가 시: 기존 Architecture 문서를 읽고 일관성 유지한다.

## 참조 파일

- `architecture-template.md`: Architecture 문서 템플릿
