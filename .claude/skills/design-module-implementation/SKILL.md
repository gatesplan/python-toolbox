---
name: design-module-implementation
description: Architecture 문서의 컴포넌트를 구체화. 적절한 패턴(CPSCP/SDW)을 선택하고 계층 구조, 디렉토리 구조, moduleinfo 문서를 작성한다.
version: 2.0.0
---

# Design Module Implementation

**2단계: 모듈 구체 설계**

Architecture 문서에서 정의된 컴포넌트를 선택하여 구체적인 구현 설계를 수행한다.
적절한 패턴을 선택하고, 계층 구조와 디렉토리 구조를 정의한다.

## 작업 목표

- Architecture 문서의 특정 컴포넌트에 대한 구체 설계
- 적절한 패턴 선택 (CPSCP vs SDW)
- 계층별 책임 정의
- 디렉토리 구조 설계
- moduleinfo 문서 초안 작성

## 전제조건

- Architecture - *.md 문서가 이미 작성되어 있어야 함
- 구체화할 컴포넌트가 명확해야 함


## 작업 프로세스

### 1. Architecture 문서 확인
- 해당 컴포넌트의 역할과 책임 파악
- 다른 컴포넌트와의 관계 분석
- 요구사항 이해

### 2. 패턴 선택
컴포넌트의 특성을 분석하여 적절한 패턴 선택:

**CPSCP (Controller-Plugin-Service-Core-Particles)**
- **선택 기준**: 단일 도메인, 일방적 의존성, 계층적 구조
- 상세: `controller-plugin-service-core-particles.md`

**SDW (Service-Director-Worker)**
- **선택 기준**: 작업 다양성, 산발적 의존성, 높은 확장성
- 상세: `service-director-worker.md`

### 3. 계층 구조 설계
- 선택한 패턴에 따라 계층 정의
- 각 계층의 책임 명시
- 계층 간 의존성 정의

### 4. 디렉토리 구조 설계
- 패턴별 표준 디렉토리 구조 적용
- moduleinfo 문서 위치 결정
- 파일 네이밍 컨벤션 적용

### 5. moduleinfo 초안 작성
- 각 계층/서브모듈에 대한 moduleinfo 문서 작성
- 두 가지 형식 활용:
  - **모듈 수준**: 여러 모듈의 목적과 책임 간단히 (메서드 나열 안 함)
  - **클래스 수준**: 하나의 모듈 상세 설명 (**input/output 타입힌트 명확히 정의**)
- 템플릿: `for-agent-moduleinfo-template.md` 참조

## Pattern Selection Guide

### CPSCP (Controller-Plugin-Service-Core-Particles)

**일반적인 패턴**. 하나의 도메인을 전담하는 모듈을 만들 때 대부분의 경우 적합한 패턴.
의존성이 Particles → Controller 방향으로 일방적으로 흐르고, 탑다운 방식으로 설계하기 쉽다.

**적용 예시:**
- 금융 지표 계산 모듈
- 데이터 변환/처리 모듈
- 단일 도메인 비즈니스 로직

상세한 설계 원칙은 `controller-plugin-service-core-particles.md` 참조.

### SDW (Service-Director-Worker)

**특정 요구사항을 만족할 때 선택**하는 패턴:
- 작업이 매우 다양하고
- 작업 간 의존성이 산발적이며
- 높은 확장성이 필수적인 경우

엔트리포인트 역할의 Service 계층 - 동작 조율을 담당하는 Director - 단일 동작을 담당하는 Worker로 이뤄짐.

**적용 예시:**
- 거래 체결 시뮬레이션
- 복잡한 데이터 파이프라인
- 동적 작업 조합이 필요한 경우

상세한 설계 원칙은 `service-director-worker.md` 참조.

## 출력물

- 선택된 패턴 및 선택 이유
- 계층별 책임 정의
- 디렉토리 구조
- 각 계층/서브모듈의 moduleinfo 문서 초안

## Followup Guide

- 패턴 선택이 불분명할 시: 두 패턴의 장단점을 비교하여 사용자에게 의견을 묻는다.
- 사용자 요구에 맞는 적절한 패턴이 없다고 판단할 시: 전통적인 설계 원칙에 기반해 확장성을 고려한 설계 제안하고, 적절한 패턴이 없으므로 work-specific한 설계를 제안함을 사용자에게 알린다.
- 설계에 있어 판단이 필요한 불분명한 사항이 있을 시: 마음대로 작업하지 말고 사용자의 의견을 확인한다.

## 참조 파일

- `controller-plugin-service-core-particles.md`: CPSCP 패턴 상세 가이드
- `service-director-worker.md`: SDW 패턴 상세 가이드
- `for-agent-moduleinfo-template.md`: moduleinfo 문서 템플릿 (모듈 수준/클래스 수준)