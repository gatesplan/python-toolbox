# 가격 샘플링

from __future__ import annotations
import numpy as np
from simple_logger import func_logging


class PriceSampler:

    @staticmethod
    @func_logging(level="DEBUG")
    def calculate_normal_params(
        range_min: float,
        range_max: float,
        std_factor: int = 4
    ) -> tuple[float, float]:
        # 범위로부터 정규분포 파라미터 계산
        mean = (range_min + range_max) / 2
        std = (range_max - range_min) / std_factor
        return mean, std

    @staticmethod
    @func_logging(level="DEBUG")
    def sample_from_normal(
        min_price: float,
        max_price: float,
        mean: float,
        std: float,
        min_z: float = -2.0,
        max_z: float = 2.0
    ) -> float:
        # 정규분포 기반 가격 샘플링 (범위 클리핑 적용)
        z_score = np.random.normal(0, 1)
        z_score = np.clip(z_score, min_z, max_z)
        price = mean + z_score * std
        return np.clip(price, min_price, max_price)
