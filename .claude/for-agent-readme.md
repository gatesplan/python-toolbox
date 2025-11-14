# 프로그래밍 AI에이전트 작업 프로토콜
- 이 문서는 AI에이전트의 원활한 작업을 위한 설계 지침이다.
- 모든 에이전트는 작업에 이 문서를 따라야 한다.
- 이 파일은 루트 폴더의 중앙 지침이므로 에이전트는 절대 이 파일을 수정하지 않는다.

## 0. 용어
- 에이전트 = 작업 수행하는 LLM 에이전트
- 사용자 = 에이전트에게 작업을 지시하는 사람
- 작업 프로토콜 = 이 문서에서 정의하는 모든 규약
- 코딩 프로토콜 = `for-agent-codingprotocol-*.md` 형식의 문서에서 정의하는 모든 코딩 스타일 및 규칙
- 환경 프로토콜 = `for-agent-envprotocol-*.md` 형식의 문서에서 정의하는 모든 환경 규약
- 디버깅 프로토콜 = `for-agent-troubleshootingprotocol.md` 형식의 문서에서 정의하는 모든 규약
- 기술문서 = `for-agent-moduleinfo.md` 형식의, 각 모듈에 대한 모든 종류의 설명서 

## 0. 작업 전 수행사항
- 코딩 프로토콜 문서 `@.claude/for-agent-codingprotocol-python.md`를 반드시 읽고, 이후 작업을 준비할 것.

## 1. 중복 구현 회피 및 기술문서 활용
- 각각의 모듈 폴더에 기술문서 `for-agent-moduleinfo.md`를 작성한다. `__init__.py` 파일과 함께 작성하며, 
해당 디렉토리에 있는 각 모듈에 대한 기능의 간단한 목적과 정보를 설명한다.
- 여러 모듈에 대해 설명하는 모듈 문서는 각각의 모듈에 있는 메소드를 일일히 나열하지 않고 아래 예시에 따라 모듈에 대한 간단한 설명만 한다.
```
    # modulename
    모듈의 목적과 책임범위에 대한 간단한 설명

    property: type = default    # 간단한 설명
    property: type = default    # 간단한 설명
    method(args: type, args: type = default) -> return_type
        raise ExceptionOrError
        메서드의 간단한 설명

    # modulename
    모듈의 목적과 책임범위에 대한 간단한 설명

    property: type = default    # 간단한 설명
    property: type = default    # 간단한 설명
    method(args: type, args: type = default) -> return_type
        raise ExceptionOrError
        메서드의 간단한 설명

    ...
```
- 하나의 모듈에 대하여 설명하는 모듈 문서는 메서드를 다음 예시와 같이 설명한다.
```
    # modulename
    모듈의 목적과 책임범위에 대한 간단한 설명

    property: type = default    # 간단한 설명
    property: type = default    # 간단한 설명

    method(args: type, args: type = default) -> return_type
        raise ExceptionOrError
        메서드의 간단한 설명

    method usecase

    ...
```
