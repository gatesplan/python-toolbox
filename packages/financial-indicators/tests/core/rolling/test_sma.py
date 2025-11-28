import numpy as np
import pytest
from financial_indicators.core.rolling.sma import sma


class TestSMA:
    """SMA 함수 테스트"""

    def test_basic_calculation(self):
        """기본 SMA 계산"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(arr, window=3)
        expected = np.array([1.0, 1.5, 2.0, 3.0, 4.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_window_equals_length(self):
        """window가 배열 길이와 같은 경우"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(arr, window=5)
        # cumulative mean 반환
        expected = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_window_greater_than_length(self):
        """window가 배열 길이보다 큰 경우"""
        arr = np.array([1.0, 2.0, 3.0])
        result = sma(arr, window=5)
        # cumulative mean 반환
        expected = np.array([1.0, 1.5, 2.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_window_one(self):
        """window=1인 경우 원본 배열 반환"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(arr, window=1)
        np.testing.assert_array_equal(result, arr)

    def test_empty_array(self):
        """빈 배열 처리"""
        arr = np.array([])
        result = sma(arr, window=3)
        assert len(result) == 0

    def test_window_less_than_one(self):
        """window < 1인 경우 예외 발생"""
        arr = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="window must be >= 1"):
            sma(arr, window=0)

    def test_output_length_equals_input(self):
        """출력 길이는 항상 입력과 동일"""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        result = sma(arr, window=3)
        assert len(result) == len(arr)

    def test_with_real_prices(self):
        """실제 가격 데이터로 테스트"""
        prices = np.array([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])
        result = sma(prices, window=3)
        # 수동 계산:
        # [0] = 100
        # [1] = (100+102)/2 = 101
        # [2] = (100+102+101)/3 = 101
        # [3] = (102+101+103)/3 = 102
        # [4] = (101+103+105)/3 = 103
        # [5] = (103+105+104)/3 = 104
        # [6] = (105+104+106)/3 = 105
        expected = np.array([100.0, 101.0, 101.0, 102.0, 103.0, 104.0, 105.0])
        np.testing.assert_array_almost_equal(result, expected)
