import numpy as np
import pandas as pd
import pytest
from financial_indicators.indicators.sma import calculate_sma


def create_test_candle_df(length=10):
    return pd.DataFrame({
        'timestamp': np.arange(1609459200, 1609459200 + length * 86400, 86400),
        'open': np.array([100.0 + i for i in range(length)]),
        'high': np.array([105.0 + i for i in range(length)]),
        'low': np.array([95.0 + i for i in range(length)]),
        'close': np.array([102.0 + i for i in range(length)]),
        'volume': np.array([1000.0 + i * 10 for i in range(length)])
    })


class TestCalculateSMA:
    def test_basic_calculation(self):
        df = create_test_candle_df(7)
        result = calculate_sma(df, period=3)

        # close: [102, 103, 104, 105, 106, 107, 108]
        # SMA[0] = 102 (cumulative)
        # SMA[1] = 102.5 (cumulative)
        # SMA[2] = (102+103+104)/3 = 103
        # SMA[3] = (103+104+105)/3 = 104
        # SMA[4] = (104+105+106)/3 = 105

        assert len(result) == len(df)
        np.testing.assert_almost_equal(result[0], 102.0)
        np.testing.assert_almost_equal(result[1], 102.5)
        np.testing.assert_almost_equal(result[2], 103.0)
        np.testing.assert_almost_equal(result[3], 104.0)
        np.testing.assert_almost_equal(result[4], 105.0)

    def test_default_period(self):
        df = create_test_candle_df(25)
        result = calculate_sma(df)
        assert len(result) == len(df)

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = calculate_sma(df, period=3)
        assert len(result) == 0

    def test_missing_close_column(self):
        df = pd.DataFrame({
            'timestamp': [1, 2, 3],
            'open': [100.0, 101.0, 102.0]
        })
        with pytest.raises(ValueError, match="'close' column"):
            calculate_sma(df, period=3)

    def test_invalid_period(self):
        df = create_test_candle_df()
        with pytest.raises(ValueError, match="period must be >= 1"):
            calculate_sma(df, period=0)

    def test_output_length_equals_input(self):
        df = create_test_candle_df(20)
        result = calculate_sma(df, period=5)
        assert len(result) == len(df)

    def test_return_type(self):
        df = create_test_candle_df()
        result = calculate_sma(df, period=3)
        assert isinstance(result, np.ndarray)
