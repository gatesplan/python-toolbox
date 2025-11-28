import numpy as np
import pandas as pd
import pytest
from financial_indicators.indicators.rsi import calculate_rsi


def create_test_candle_df(length=10):
    return pd.DataFrame({
        'timestamp': np.arange(1609459200, 1609459200 + length * 86400, 86400),
        'open': np.array([100.0 + i for i in range(length)]),
        'high': np.array([105.0 + i for i in range(length)]),
        'low': np.array([95.0 + i for i in range(length)]),
        'close': np.array([102.0 + i for i in range(length)]),
        'volume': np.array([1000.0 + i * 10 for i in range(length)])
    })


class TestCalculateRSI:
    def test_basic_calculation(self):
        df = pd.DataFrame({
            'close': [44.0, 44.25, 44.375, 44.5, 43.75, 44.0, 44.25,
                      44.75, 45.0, 45.5, 45.75, 46.0, 45.875, 46.125,
                      46.0]
        })
        result = calculate_rsi(df, period=14)

        assert len(result) == len(df)
        assert result[0] >= 0 and result[0] <= 100
        assert not np.isnan(result[-1])

    def test_trending_up(self):
        df = create_test_candle_df(20)
        result = calculate_rsi(df, period=14)

        assert len(result) == len(df)
        assert result[-1] > 50

    def test_default_period(self):
        df = create_test_candle_df(20)
        result = calculate_rsi(df)
        assert len(result) == len(df)

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = calculate_rsi(df, period=14)
        assert len(result) == 0

    def test_missing_column(self):
        df = pd.DataFrame({
            'timestamp': [1, 2, 3],
            'open': [100.0, 101.0, 102.0]
        })
        with pytest.raises(ValueError, match="'close' column"):
            calculate_rsi(df, period=14)

    def test_custom_column(self):
        df = create_test_candle_df(20)
        result = calculate_rsi(df, period=14, use='high')
        assert len(result) == len(df)

    def test_invalid_period(self):
        df = create_test_candle_df()
        with pytest.raises(ValueError, match="period must be >= 1"):
            calculate_rsi(df, period=0)

    def test_output_length_equals_input(self):
        df = create_test_candle_df(30)
        result = calculate_rsi(df, period=14)
        assert len(result) == len(df)

    def test_return_type(self):
        df = create_test_candle_df()
        result = calculate_rsi(df, period=14)
        assert isinstance(result, np.ndarray)

    def test_range_0_to_100(self):
        df = create_test_candle_df(30)
        result = calculate_rsi(df, period=14)
        assert np.all((result >= 0) & (result <= 100))
