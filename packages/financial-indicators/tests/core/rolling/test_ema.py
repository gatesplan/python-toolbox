import numpy as np
import pytest
from financial_indicators.core.rolling.ema import ema


class TestEMA:
    """EMA 함수 테스트"""

    def test_basic_calculation(self):
        """기본 EMA 계산"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ema(arr, span=3)

        # alpha = 2/(3+1) = 0.5
        # EMA[0] = 1.0
        # EMA[1] = 0.5*2 + 0.5*1 = 1.5
        # EMA[2] = 0.5*3 + 0.5*1.5 = 2.25
        # EMA[3] = 0.5*4 + 0.5*2.25 = 3.125
        # EMA[4] = 0.5*5 + 0.5*3.125 = 4.0625
        expected = np.array([1.0, 1.5, 2.25, 3.125, 4.0625])
        np.testing.assert_array_almost_equal(result, expected)

    def test_empty_array(self):
        """빈 배열 처리"""
        arr = np.array([])
        result = ema(arr, span=3)
        assert len(result) == 0

    def test_span_less_than_one(self):
        """span < 1인 경우 예외 발생"""
        arr = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="span must be >= 1"):
            ema(arr, span=0)

    def test_output_length_equals_input(self):
        """출력 길이는 항상 입력과 동일"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        result = ema(arr, span=5)
        assert len(result) == len(arr)

    def test_single_element(self):
        """단일 원소 배열"""
        arr = np.array([10.0])
        result = ema(arr, span=3)
        np.testing.assert_array_almost_equal(result, arr)
