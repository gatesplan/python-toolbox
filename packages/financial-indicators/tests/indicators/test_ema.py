import numpy as np
import pandas as pd
import pytest
from financial_indicators.indicators.ema import calculate_ema


def create_test_candle_df(length=10):
    return pd.DataFrame({
        'timestamp': np.arange(1609459200, 1609459200 + length * 86400, 86400),
        'open': np.array([100.0 + i for i in range(length)]),
        'high': np.array([105.0 + i for i in range(length)]),
        'low': np.array([95.0 + i for i in range(length)]),
        'close': np.array([102.0 + i for i in range(length)]),
        'volume': np.array([1000.0 + i * 10 for i in range(length)])
    })


class TestCalculateEMA:
    def test_basic_calculation(self):
        df = create_test_candle_df(5)
        result = calculate_ema(df, period=3)

        # close: [102, 103, 104, 105, 106]
        # alpha = 2 / (3 + 1) = 0.5
        # EMA[0] = 102
        # EMA[1] = 0.5 * 103 + 0.5 * 102 = 102.5
        # EMA[2] = 0.5 * 104 + 0.5 * 102.5 = 103.25
        # EMA[3] = 0.5 * 105 + 0.5 * 103.25 = 104.125
        # EMA[4] = 0.5 * 106 + 0.5 * 104.125 = 105.0625

        assert len(result) == len(df)
        np.testing.assert_almost_equal(result[0], 102.0)
        np.testing.assert_almost_equal(result[1], 102.5)
        np.testing.assert_almost_equal(result[2], 103.25)
        np.testing.assert_almost_equal(result[3], 104.125)
        np.testing.assert_almost_equal(result[4], 105.0625)

    def test_default_period(self):
        df = create_test_candle_df(15)
        result = calculate_ema(df)
        assert len(result) == len(df)

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = calculate_ema(df, period=3)
        assert len(result) == 0

    def test_missing_close_column(self):
        df = pd.DataFrame({
            'timestamp': [1, 2, 3],
            'open': [100.0, 101.0, 102.0]
        })
        with pytest.raises(ValueError, match="'close' column"):
            calculate_ema(df, period=3)

    def test_invalid_period(self):
        df = create_test_candle_df()
        with pytest.raises(ValueError, match="period must be >= 1"):
            calculate_ema(df, period=0)

    def test_output_length_equals_input(self):
        df = create_test_candle_df(20)
        result = calculate_ema(df, period=5)
        assert len(result) == len(df)

    def test_return_type(self):
        df = create_test_candle_df()
        result = calculate_ema(df, period=3)
        assert isinstance(result, np.ndarray)
