---
name: design-module-architecture
description: Python 모듈 아키텍처 설계 시 적절한 패턴을 선택하고 Architecture - *.md 설계 문서를 작성. 새 모듈 개발 계획을 세우거나 기존 모듈 리팩토링 시 사용한다.
version: 1.0.0
---

# Design Module Architecture

사용자의 의도에 맞는 적절한 설계 패턴을 찾아 설계 초안 문서(Architecture - *.md)를 작성한다. 
이 설계 문서 작성 과정에서 고려할 것은 다음과 같다.

1. 깔끔한 컴포넌트 관계도
2. 목표 지정 위주의 **지나치게 구체적이지 않은** 가이드라인 설계

설계 초안 템플릿은 `architecture-document-template.md` 참조.


## Service Pattern Guide

### Service-Director-Worker
 
3개 계층으로 이뤄진 단일 서비스용 패턴. 
엔트리포인트 역할의 Service 계층 - 동작 조율을 담당하는 Director - 단일 동작을 담당하는 Worker로 이뤄짐. 
상세한 설계 원칙은 `service-director-worker.md` 참조.


## Followup Guide

- 사용자 요구에 맞는 적절한 패턴이 없다고 판단할 시: 전통적인 설계 원칙에 기반해 확장성을 고려한 설계 제안하고, 적절한 패턴이 없으므로 work-specific한 설계를 제안함을 사용자에게 알린다.
- 설계에 있어 판단이 필요한 불분명한 사항이 있을 시: 마음대로 작업하지 말고 사용자의 의견을 확인한다.