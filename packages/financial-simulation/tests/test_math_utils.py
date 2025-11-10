import pytest
import sys
from pathlib import Path

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from financial_simulation.tradesim.Core import MathUtils


class TestMathUtils:

    def test_round_to_min_unit_positive(self):
        # 양수 정상 케이스
        result = MathUtils.round_to_min_unit(10.5, 0.5)
        assert result == 10.5

        result = MathUtils.round_to_min_unit(10.7, 0.5)
        assert result == 10.5

        result = MathUtils.round_to_min_unit(100.0, 10.0)
        assert result == 100.0

    def test_round_to_min_unit_zero(self):
        # 0 처리
        result = MathUtils.round_to_min_unit(0.0, 0.5)
        assert result == 0.0

    def test_round_to_min_unit_negative(self):
        # 음수 처리 (0 반환)
        result = MathUtils.round_to_min_unit(-10.0, 0.5)
        assert result == 0.0

    def test_round_to_min_unit_edge_cases(self):
        # 경계값
        result = MathUtils.round_to_min_unit(0.001, 0.01)
        assert result == 0.0

        result = MathUtils.round_to_min_unit(0.01, 0.01)
        assert result == 0.01

        result = MathUtils.round_to_min_unit(0.015, 0.01)
        assert result == 0.01
