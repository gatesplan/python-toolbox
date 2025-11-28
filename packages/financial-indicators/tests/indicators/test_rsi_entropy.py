import numpy as np
import pandas as pd
import pytest
from financial_indicators.indicators.rsi_entropy import calculate_rsi_entropy


def create_test_candle_df(length=400):
    np.random.seed(42)
    base = 100.0
    prices = base + np.cumsum(np.random.randn(length) * 0.5)

    return pd.DataFrame({
        'timestamp': np.arange(1609459200, 1609459200 + length * 86400, 86400),
        'open': prices + np.random.randn(length) * 0.1,
        'high': prices + np.abs(np.random.randn(length) * 0.5),
        'low': prices - np.abs(np.random.randn(length) * 0.5),
        'close': prices,
        'volume': np.random.rand(length) * 1000 + 500
    })


class TestCalculateRSIEntropy:
    def test_basic_calculation(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df, rsi_period=20, entropy_window=365)

        assert isinstance(result, dict)
        assert len(result) == 5

    def test_return_type(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df)

        assert isinstance(result, dict)
        for key, value in result.items():
            assert isinstance(value, np.ndarray)

    def test_keys(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df)

        expected_keys = {'base', 'z-1', 'z+1', 'buy', 'sell'}
        assert set(result.keys()) == expected_keys

    def test_array_lengths(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df)

        for key, value in result.items():
            assert len(value) == len(df), f"Key '{key}' has wrong length"

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = calculate_rsi_entropy(df)

        assert isinstance(result, dict)
        assert len(result) == 5
        for value in result.values():
            assert len(value) == 0

    def test_missing_column(self):
        df = pd.DataFrame({
            'timestamp': [1, 2, 3],
            'open': [100.0, 101.0, 102.0]
        })
        with pytest.raises(ValueError, match="'close' column"):
            calculate_rsi_entropy(df)

    def test_custom_column(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df, rsi_use='high')

        assert isinstance(result, dict)
        assert len(result) == 5

    def test_invalid_rsi_period(self):
        df = create_test_candle_df(400)
        with pytest.raises(ValueError, match="rsi_period must be >= 1"):
            calculate_rsi_entropy(df, rsi_period=0)

    def test_invalid_entropy_window(self):
        df = create_test_candle_df(400)
        with pytest.raises(ValueError, match="entropy_window must be >= 2"):
            calculate_rsi_entropy(df, entropy_window=1)

    def test_value_ranges(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df)

        assert np.all((result['base'] >= 0) & (result['base'] <= 1))

        z_minus_valid = result['z-1'][~np.isnan(result['z-1'])]
        assert np.all((z_minus_valid >= -1) & (z_minus_valid <= 2))

        z_plus_valid = result['z+1'][~np.isnan(result['z+1'])]
        assert np.all((z_plus_valid >= -1) & (z_plus_valid <= 2))

        buy_valid = result['buy'][~np.isnan(result['buy'])]
        assert np.all((buy_valid >= 0) & (buy_valid <= 1))

        sell_valid = result['sell'][~np.isnan(result['sell'])]
        assert np.all((sell_valid >= 0) & (sell_valid <= 1))

    def test_default_parameters(self):
        df = create_test_candle_df(400)
        result = calculate_rsi_entropy(df)

        assert isinstance(result, dict)
        assert len(result) == 5
