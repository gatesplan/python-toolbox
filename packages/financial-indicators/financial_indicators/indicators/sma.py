import numpy as np
import pandas as pd
from ..core.rolling import sma as core_sma
from ..registry import register


@register("sma")
def calculate_sma(candle_df: pd.DataFrame, period: int = 20) -> np.ndarray:
    if len(candle_df) == 0:
        return np.array([])

    if 'close' not in candle_df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    if period < 1:
        raise ValueError("period must be >= 1")

    close_prices = candle_df['close'].values
    return core_sma(close_prices, window=period)
