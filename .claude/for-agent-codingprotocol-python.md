# Python Coding Protocol for Agent
- 이 문서는 에이전트의 원활하고 균일한 Python 코딩을 위한 프로토콜이다.
- 모든 에이전트는 Python 언어 사용시 이 코딩 프로토콜을 준수해야 한다.
- 이 파일은 루트 폴더의 중앙 지침이므로 에이전트는 절대 이 파일을 수정하지 않는다.

## 중요 규칙
- 하나의 파일은 오직 하나의 함수 또는 하나의 클래스만 포함한다.
- 모듈 클래스의 파일명과 클래스명은 CamelCase로 작성한다.
- 예외 클래스는 책임 모듈 폴더 아래에 위치한다.
- 클래스는 항상 단일 책임 원칙을 따른다.

## 문서화 규칙
- 모든 문서화는 `for-agent-moduleinfo.md` 파일 작성으로 충분하다.
- 코드 내에서는 한줄 주석(`#`)만 사용한다.
- Docstring(""" """), 멀티라인 주석, 함수/클래스 설명 주석 등 모든 문서화 주석은 작성하지 않거나 한 줄로 간단히 쓴다.
- 코드의 동작이나 구조 설명은 `for-agent-moduleinfo.md`에만 작성한다.

### 코드 예시
```python
# 사용자 인증을 처리하는 서비스
class AuthService:
    def __init__(self, token_manager):
        self.token_manager = token_manager

    def login(self, username, password):
        # 정보가 맞지 않을 경우 에러
        if not username or not password:
            raise ValueError("Invalid credentials")
        
        # 토큰 생성 및 반환
        token = self.token_manager.generate(username)
        return token

    def validate_token(self, token):
        return self.token_manager.verify(token)

    def logout(self, token):
        self.token_manager.revoke(token)
```

## 코드 품질 관리를 위한 세부 사항

### 1. `import` 규칙

임포트는 기본적으로 Python PEP 8 스타일 가이드에 따르며, Type checking 대상인지 여부는 패키지 의존성 확인을 거쳐 필요시 사용.


### 2. 로깅 규칙

`simple-logger` 패키지 사용.

```bash
pip install git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/simple-logger
```

각 함수와 메서드는 `@func_logging` 데코레이터를 사용해 로깅한다. 구체적인 사용법은 simple-logger의 readme 참조 할 것.

주요 비즈니스 로직 메서드만 INFO 레벨, 파라메터, 결과 로깅을 하고, 실행시간 측정은 하지 않는다.

(level='INFO', log_params=True, log_result=True)

```python
from simple_logger import func_logging, logger

# 기본: DEBUG 레벨, 시작/종료만
@func_logging
def helper_function():
    logger.info("작업 수행 중...")
    return "완료"

# 비즈니스 로직: INFO 레벨 + 파라미터 + 실행시간
@func_logging(level="INFO", log_params=True, log_time=True)
def process_order(order_id: int, amount: float):
    logger.info(f"주문 {order_id} 처리 중")
    return True

# 모든 옵션 사용
@func_logging(level="INFO", log_params=True, log_result=True, log_time=True)
def calculate(x: int, y: int) -> int:
    return x + y
```

각 클래스는 초기화시 전용 데코레이터로 INFO 레벨 로깅한다.

```python
from simple_logger import init_logging, func_logging, logger

class OrderService:
    @init_logging(level="INFO", log_params=True)
    def __init__(self, db_url: str):
        self.db_url = db_url

    @func_logging(level="INFO", log_time=True)
    def create_order(self, user_id: int):
        logger.info(f"주문 생성: user_id={user_id}")
        return {"order_id": 123}
```

하나의 메서드 동작 과정에서 중요 단계가 있다면 DEBUG 레벨 로깅한다.