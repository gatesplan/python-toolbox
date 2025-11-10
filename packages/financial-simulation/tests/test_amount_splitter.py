import pytest
import sys
from pathlib import Path
import numpy as np

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from financial_simulation.tradesim.Core import AmountSplitter


class TestAmountSplitter:

    def test_split_single_count(self):
        # split_count=1일 때 전체 반환
        result = AmountSplitter.split_with_dirichlet(100.0, 0.01, 1)

        assert len(result) == 1
        assert result[0] == 100.0

    def test_split_multiple_count(self):
        # split_count=3
        np.random.seed(42)
        result = AmountSplitter.split_with_dirichlet(100.0, 0.01, 3)

        assert len(result) >= 1
        assert len(result) <= 3

    def test_split_sum_preserved(self):
        # 총합 보존
        np.random.seed(42)

        for _ in range(10):
            result = AmountSplitter.split_with_dirichlet(100.0, 0.01, 3)
            assert abs(sum(result) - 100.0) < 0.0001

    def test_split_min_amount_constraint(self):
        # 최소 단위 제약 (각 조각이 min_amount의 배수)
        np.random.seed(42)

        result = AmountSplitter.split_with_dirichlet(100.0, 0.5, 3)

        # 마지막 조각 제외 (잔여량이 추가될 수 있음)
        for piece in result[:-1]:
            if piece > 0:
                # 0.5의 배수인지 확인 (부동소수점 오차 고려)
                remainder = piece % 0.5
                assert remainder < 0.0001 or remainder > 0.4999

    def test_split_zero_pieces_handling(self):
        # 0 조각 제거 및 base 전량 반환 처리
        np.random.seed(42)

        # min_amount가 너무 크면 모두 0으로 내림 → base 전량 반환
        result = AmountSplitter.split_with_dirichlet(1.0, 10.0, 3)

        assert len(result) == 1
        assert result[0] == 1.0
