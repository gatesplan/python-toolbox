# simple-logger

loguru 기반 로거 래퍼. 데코레이터로 함수/메서드의 시작/종료를 자동 로깅하고, 파라미터/반환값/실행시간을 선택적으로 기록할 수 있습니다.

## 설치

```bash
pip install git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/simple-logger
```

## 기본 사용법

### 1. 로거 설정 (선택사항)

```python
from simple_logger import configure_logger

# 기본 설정으로 사용 (자동 초기화됨)
# 또는 커스터마이징

# 파일 크기 기반 로테이션
configure_logger(
    log_dir="./logs",
    console_level="INFO",
    file_level="DEBUG",
    rotation="500 MB",          # 500MB마다 새 파일
    retention="10 days"
)

# 시간 기반 로테이션
configure_logger(
    log_dir="./logs",
    console_level="INFO",
    file_level="DEBUG",
    rotation="1 day",           # 매일 자정에 새 파일
    retention="30 days"
)
```

### 2. 함수/메서드 로깅

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

### 3. 클래스 초기화 로깅

```python
from simple_logger import init_logging, func_logging

class OrderService:
    @init_logging(level="INFO", log_params=True)
    def __init__(self, db_url: str):
        self.db_url = db_url

    @func_logging(level="INFO", log_time=True)
    def create_order(self, user_id: int):
        logger.info(f"주문 생성: user_id={user_id}")
        return {"order_id": 123}
```

### 4. 직접 로깅

```python
from simple_logger import logger

logger.debug("디버그 메시지")
logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")
logger.exception("예외 메시지")  # 스택트레이스 포함
```

## 로그 출력 예시

```
[25-10-03 14:30:15] [DEBUG   ] [OrderService|create_order] 시작
[25-10-03 14:30:15] [INFO    ] [OrderService|create_order] 주문 생성: user_id=123
[25-10-03 14:30:15] [DEBUG   ] [OrderService|create_order] 종료 elapsed=0.003s
```

## 데코레이터 옵션

### `@func_logging` 옵션

- `level`: 로그 레벨 (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`)
- `log_params`: 함수 파라미터 로깅 여부 (기본: `False`)
- `log_result`: 반환값 로깅 여부 (기본: `False`)
- `log_time`: 실행 시간 측정 여부 (기본: `False`)

### `@init_logging` 옵션

- `level`: 로그 레벨
- `log_params`: 파라미터 로깅 여부

## 특징

- **loguru 기반**: 강력한 로그 로테이션, 비동기 지원 등
- **자동 컨텍스트**: 클래스명/함수명 자동 추적
- **유연한 설정**: 콘솔/파일 레벨 개별 설정 가능
- **깔끔한 인터페이스**: 데코레이터만 추가하면 끝
