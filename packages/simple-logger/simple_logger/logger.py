"""Simple Logger - loguru 기반 로거 래퍼"""

import time
from functools import wraps
from typing import Callable, Any, Optional
from pathlib import Path
from datetime import datetime

from loguru import logger


def configure_logger(
    log_dir: Optional[str] = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "500 MB",
    retention: str = "10 days",
    format_string: Optional[str] = None
):
    """로거 초기 설정

    Args:
        log_dir: 로그 파일 디렉토리 경로. None이면 './logs'
        console_level: 콘솔 출력 레벨 (DEBUG, INFO, WARNING, ERROR)
        file_level: 파일 출력 레벨
        rotation: 로그 파일 로테이션 조건 (예: "500 MB", "1 day")
        retention: 로그 파일 보관 기간 (예: "10 days")
        format_string: 커스텀 포맷 문자열. None이면 기본 포맷 사용
    """
    # 기존 핸들러 제거
    logger.remove()

    # 기본 포맷
    if format_string is None:
        format_string = (
            "[<green>{time:YY-MM-DD HH:mm:ss}</green>] "
            "[<level>{level: <8}</level>] "
            "[<cyan>{extra[class_name]}</cyan>|<cyan>{extra[func_id]}</cyan>] "
            "<level>{message}</level>"
        )

    # 콘솔 핸들러
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format=format_string,
        level=console_level,
        colorize=True
    )

    # 파일 핸들러
    if log_dir is None:
        log_dir = "./logs"

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    log_file = log_path / f"log_{timestamp}.log"

    logger.add(
        sink=str(log_file),
        format=format_string,
        level=file_level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8"
    )

    # 기본 컨텍스트 설정
    logger.configure(extra={"class_name": "-", "func_id": "-"})


def func_logging(
    _func: Optional[Callable] = None,
    *,
    level: str = "DEBUG",
    log_params: bool = False,
    log_result: bool = False,
    log_time: bool = False
) -> Callable:
    """함수/메서드 실행 자동 로깅 데코레이터

    사용법:
        @func_logging  # 기본값: DEBUG 레벨, 시작/종료만
        def helper():
            ...

        @func_logging(level="INFO", log_params=True, log_time=True)
        def business_logic(user_id):
            ...

    Args:
        level: 로그 레벨 ("DEBUG" | "INFO" | "WARNING" | "ERROR")
        log_params: 함수 파라미터 로깅 여부
        log_result: 반환값 로깅 여부
        log_time: 실행 시간 측정 여부
    """
    def decorator(func: Callable) -> Callable:
        func_name = func.__name__
        qual_parts = func.__qualname__.split('.')
        is_method = len(qual_parts) > 1
        class_name = qual_parts[0] if is_method else "-"
        func_id = f'{class_name}.{func_name}' if is_method else func_name

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 컨텍스트 바인딩
            ctx_logger = logger.bind(class_name=class_name, func_id=func_id)

            # 시작 로그
            start_msg = "시작"
            if log_params:
                # 파라미터 수집 (self 제외)
                params = {}
                if is_method and args:
                    # 메서드인 경우 self 제외
                    param_args = args[1:]
                else:
                    param_args = args

                # args를 딕셔너리로 변환 (간단하게)
                if param_args:
                    params['args'] = param_args
                if kwargs:
                    params['kwargs'] = kwargs

                if params:
                    start_msg += f" params={params}"

            ctx_logger.log(level, start_msg)

            # 실행
            start_time = time.time() if log_time else None
            try:
                result = func(*args, **kwargs)

                # 종료 로그
                end_msg = "종료"
                if log_result:
                    end_msg += f" result={result}"
                if log_time:
                    elapsed = time.time() - start_time
                    end_msg += f" elapsed={elapsed:.3f}s"

                ctx_logger.log(level, end_msg)
                return result

            except Exception as e:
                ctx_logger.exception("오류 발생")
                raise

        return wrapper

    # 인자 없이 호출된 경우 (@func_logging)
    if _func is not None:
        return decorator(_func)

    # 인자와 함께 호출된 경우 (@func_logging(level="INFO"))
    return decorator


def init_logging(
    _func: Optional[Callable] = None,
    *,
    level: str = "DEBUG",
    log_params: bool = False
) -> Callable:
    """__init__ 메서드 전용 로깅 데코레이터

    사용법:
        @init_logging
        def __init__(self):
            ...

        @init_logging(level="INFO", log_params=True)
        def __init__(self, user_id):
            ...

    Args:
        level: 로그 레벨
        log_params: 파라미터 로깅 여부
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cls = args[0].__class__.__name__ if args else "Unknown"
            func_id = f'{cls}.__init__'

            ctx_logger = logger.bind(class_name=cls, func_id=func_id)

            # 시작 로그
            start_msg = "초기화 시작"
            if log_params and (args[1:] or kwargs):
                params = {}
                if len(args) > 1:
                    params['args'] = args[1:]
                if kwargs:
                    params['kwargs'] = kwargs
                start_msg += f" params={params}"

            ctx_logger.log(level, start_msg)

            try:
                result = func(*args, **kwargs)
                ctx_logger.log(level, "초기화 완료")
                return result
            except Exception:
                ctx_logger.exception("초기화 오류")
                raise

        return wrapper

    # 인자 없이 호출된 경우
    if _func is not None:
        return decorator(_func)

    # 인자와 함께 호출된 경우
    return decorator


# 기본 로거 설정 (모듈 임포트 시 자동 실행)
configure_logger()


