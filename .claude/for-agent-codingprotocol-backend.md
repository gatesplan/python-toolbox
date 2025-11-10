# 프로그래밍 AI에이전트 코딩 프로토콜 - 백엔드 개발용
- 이 문서는 백엔드 응용층(Application Tier) 개발을 담당하는 에이전트가 코드 작성시 지켜야 하는 규칙을 정의한다.
- 이 문서는 에이전트가 *절대* 수정하지 않는다.
- 응용층이란 3-tier 아키텍처에서 비즈니스 로직을 처리하는 중간 계층(백엔드 서버)을 의미한다.

## 계층 구조
- 응용층(백엔드)은 크게 5개 세부 계층으로 구분한다.

### 0. 입자층
`InternalStruct`, `Structs`, `Constants`와 같은 가장 작은 단위의 구조를 정의한다.
각 구조는 루트 바로 아래에 해당 작업 디렉터리를 가지며, 별도의 세부 폴더 없이 평평한 구조로 관리한다.

- **InternalStruct**: 모듈 내부에서만 사용되는 데이터 구조를 정의한다. 내부 데이터 교환, 컬렉션 등 외부로 노출되지 않는 모든 데이터 형식을 포함한다.
- **Structs**: 모듈 외부로 나가거나 외부에서 들어오는 데이터의 형식을 정의한다. API 요청/응답, 외부 시스템 연동 시 사용한다.
- **Constants**: 내부에서 사용하는 상수 및 Enum을 정의한다.

입자층은 다른 계층과 다르게 계층 폴더 아래에 바로 클래스 파일이 위치해야 한다. (평평한 디렉토리 구조)

```
└─{ModuleRoot}
    └─InternalStruct
        └─{SomeInternalStruct}.py
        └─{AnotherInternalStruct}.py
        └─for-agent-moduleinfo.md
    └─Structs
        └─{SomeStruct}.py
        └─{AnotherStruct}.py
        └─for-agent-moduleinfo.md
    └─Constants
        └─{SomeConstants}.py
        └─{AnotherConstants}.py
        └─for-agent-moduleinfo.md
```

### 1. 코어층 (Core)
입자층의 데이터 구조체를 직접/간접적으로 사용하여 상호 의존성이 아예 없는 단위 기능을 구현하는 계층.
외부와의 통신을 전담하거나, 저장된 데이터를 입출력하거나, 특정 기능의 가장 작은 단위를 구현하는 가장 낮은 단계의 구성요소.

```
└─{ModuleRoot}
    └─Core
        └─for-agent-moduleinfo.md       # 계층 기술문서
        └─{CoreModuleName}
            └─{CoreModuleName}.py       # 모듈 파일
            └─{Some}Exception.py        # 예외 클래스 정의 파일
            └─{Another}Exception.py     # 예외 클래스 정의 파일
            └─for-agent-moduleinfo.md   # 모듈 기술문서
```

### 2. 서비스 (Service)
응용 계층의 구성요소로, 일정한 목적에 따라 조직한 코어층 이하의 조합 또는 보다 복잡한 동작을 구현한다.
서비스는 단일 책임 원칙에 따라 세분화되어야 하며, 각 서비스는 의미있는 하나의 기능 집합만을 구현한다.
예를 들어, 하나의 큰 "결제서비스"보다는 카드결제서비스, 계좌이체결제서비스, 간편결제서비스처럼 세분화하여 구현한다.
서비스 상호간에 의존해서는 안 되며, 이는 각 서비스의 독립적인 테스트와 유지보수를 보장하기 위함이다.

```
└─{ModuleRoot}
    └─Service
        └─for-agent-moduleinfo.md          # 계층 기술문서
        └─{ServiceModuleName}
            └─{ServiceModuleName}.py       # 모듈 파일
            └─{Some}Exception.py           # 예외 클래스 정의 파일
            └─{Another}Exception.py        # 예외 클래스 정의 파일
            └─for-agent-moduleinfo.md      # 모듈 기술문서
```

### 3. 플러그인 (Plugin)
서비스 계층이 단일 책임 원칙에 따라 세분화되어 있을 때, 플러그인은 이들 중 적절한 서비스를 선택하거나 조합하는 전략 계층이다.
예를 들어, 결제플러그인은 상황에 따라 카드결제서비스, 계좌이체결제서비스, 간편결제서비스 중 하나를 선택하거나 조합하여 실행한다.
플러그인 단계에서부터 의존성 역전을 반드시 적용하며, 이는 구체적인 서비스 구현에 의존하지 않고 추상화에 의존하도록 하기 위함이다.
플러그인은 전략 패턴의 전략 객체(Strategy) 역할을 하며, 컨트롤러 계층에서 전략 소켓으로 사용된다.
컨트롤러는 플러그인의 추상화(인터페이스/추상클래스)에 의존하고, 런타임에 구체적인 플러그인 구현체를 주입받아 사용한다.
컨트롤러의 모든 기능이 플러그인을 통해 구현되어야 하는것은 아니나, 행위 기반 캡슐화나 전략 패턴이 필요할 때 선택적으로 플러그인을 구현하여 동작을 관리한다.
이 계층은 복잡한 어플리케이션에서 동작 자체의 추상화가 필요할 때 사용하는 보조 계층에 해당한다.

```
└─{ModuleRoot}
    └─Plugin
        └─for-agent-moduleinfo.md          # 계층 기술문서
        └─{PluginModuleName}.py            # 플러그인 구현 파일
```

### 4. API 계층 (API)
백엔드의 진입점으로, HTTP 요청/응답 처리와 비즈니스 로직 오케스트레이션을 담당하는 계층.
REST API 엔드포인트, GraphQL 리졸버, gRPC 서비스 등을 정의한다.
요청 검증, 인증/인가, 응답 포맷팅, 에러 핸들링을 수행하며, 서비스 또는 플러그인을 조합하여 비즈니스 로직을 실행한다.
일반적인 백엔드 프레임워크(Spring의 @RestController, Django의 View, Express의 Router)의 패턴을 따른다.

```
└─{ModuleRoot}
    └─API
        └─for-agent-moduleinfo.md          # 계층 기술문서
        └─{APIModuleName}
            └─{APIModuleName}.py           # API 엔드포인트 및 핸들러
            └─{Some}Exception.py           # 예외 클래스 정의 파일
            └─{Another}Exception.py        # 예외 클래스 정의 파일
            └─for-agent-moduleinfo.md      # 모듈 기술문서
```
