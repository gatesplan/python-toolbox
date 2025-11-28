import numpy as np
import pytest
from financial_indicators.core.series import (
    scaling, standardize, pct_change, log_return, diff, crossover, shift
)


class TestScaling:
    def test_basic_scaling(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = scaling(arr, min_val=0.0, max_val=1.0)
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_constant_array(self):
        arr = np.array([5.0, 5.0, 5.0])
        result = scaling(arr, min_val=0.0, max_val=1.0)
        expected = np.array([0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)


class TestStandardize:
    def test_basic_standardize(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize(arr)
        # 평균 = 3, std = sqrt(2.5) ≈ 1.58
        assert abs(np.mean(result)) < 1e-10
        assert abs(np.std(result, ddof=1) - 1.0) < 1e-10


class TestPctChange:
    def test_basic_pct_change(self):
        arr = np.array([100.0, 102.0, 101.0, 103.0])
        result = pct_change(arr, periods=1)
        assert np.isnan(result[0])
        np.testing.assert_almost_equal(result[1], 0.02)
        np.testing.assert_almost_equal(result[2], -0.00980392, decimal=5)


class TestDiff:
    def test_basic_diff(self):
        arr = np.array([100.0, 102.0, 101.0, 103.0, 105.0])
        result = diff(arr, periods=1)
        expected = np.array([np.nan, 2.0, -1.0, 2.0, 2.0])
        np.testing.assert_array_almost_equal(result, expected)


class TestCrossover:
    def test_basic_crossover(self):
        arr = np.array([1.0, 1.5, 3.0, 2.5, 1.0])
        reference = 2.0
        result = crossover(arr, reference)
        # [0]: 비교 불가 → 0
        # [1]: 1.0 < 2.0, 1.5 < 2.0 → 0
        # [2]: 1.5 < 2.0, 3.0 > 2.0 → 1 (상향 교차)
        # [3]: 3.0 > 2.0, 2.5 > 2.0 → 0
        # [4]: 2.5 > 2.0, 1.0 < 2.0 → -1 (하향 교차)
        expected = np.array([0, 0, 1, 0, -1])
        np.testing.assert_array_equal(result, expected)


class TestShift:
    def test_shift_positive(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = shift(arr, periods=2)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        np.testing.assert_almost_equal(result[2], 1.0)

    def test_shift_negative(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = shift(arr, periods=-1)
        np.testing.assert_almost_equal(result[0], 2.0)
        assert np.isnan(result[4])
