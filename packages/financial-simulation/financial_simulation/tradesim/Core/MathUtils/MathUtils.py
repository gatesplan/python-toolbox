# 순수 수학 유틸리티

from simple_logger import func_logging


class MathUtils:

    @staticmethod
    @func_logging(level="DEBUG")
    def round_to_min_unit(value: float, min_unit: float) -> float:
        # 값을 최소 단위의 배수로 내림
        if value <= 0:
            return 0.0
        return (value // min_unit) * min_unit
