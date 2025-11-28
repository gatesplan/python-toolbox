import numpy as np
import pandas as pd
from ..core.rolling import ema as core_ema
from ..registry import register


@register("ema")
def calculate_ema(candle_df: pd.DataFrame, period: int = 12) -> np.ndarray:
    if len(candle_df) == 0:
        return np.array([])

    if 'close' not in candle_df.columns:
        raise ValueError("DataFrame must contain 'close' column")

    if period < 1:
        raise ValueError("period must be >= 1")

    close_prices = candle_df['close'].values
    return core_ema(close_prices, span=period)
