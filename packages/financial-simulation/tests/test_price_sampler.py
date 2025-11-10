import pytest
import sys
from pathlib import Path
import numpy as np

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from financial_simulation.tradesim.Core import PriceSampler


class TestPriceSampler:

    def test_calculate_normal_params(self):
        # mean, std 계산
        mean, std = PriceSampler.calculate_normal_params(100.0, 200.0)
        assert mean == 150.0
        assert std == 25.0

        mean, std = PriceSampler.calculate_normal_params(0.0, 100.0, std_factor=5)
        assert mean == 50.0
        assert std == 20.0

    def test_sample_from_normal_range(self):
        # 범위 내 샘플링
        np.random.seed(42)

        for _ in range(100):
            price = PriceSampler.sample_from_normal(100.0, 200.0, 150.0, 25.0)
            assert 100.0 <= price <= 200.0

    def test_sample_from_normal_clipping(self):
        # z-score 클리핑 검증
        np.random.seed(42)

        samples = [
            PriceSampler.sample_from_normal(100.0, 200.0, 150.0, 25.0)
            for _ in range(1000)
        ]

        # 모든 샘플이 범위 내
        assert all(100.0 <= s <= 200.0 for s in samples)

    def test_sample_from_normal_distribution(self):
        # 분포 검증 (평균 근처)
        np.random.seed(42)

        samples = [
            PriceSampler.sample_from_normal(100.0, 200.0, 150.0, 25.0)
            for _ in range(1000)
        ]

        sample_mean = np.mean(samples)
        # 평균이 대략 150 근처 (오차 범위 ±10)
        assert 140.0 <= sample_mean <= 160.0
