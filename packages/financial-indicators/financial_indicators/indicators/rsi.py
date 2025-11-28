import numpy as np
import pandas as pd
from ..registry import register


@register("rsi")
def calculate_rsi(candle_df: pd.DataFrame, period: int = 14, use: str = 'close') -> np.ndarray:
    if len(candle_df) == 0:
        return np.array([])

    if use not in candle_df.columns:
        raise ValueError(f"DataFrame must contain '{use}' column")

    if period < 1:
        raise ValueError("period must be >= 1")

    prices = candle_df[use].values
    delta = np.diff(prices, prepend=prices[0])

    gains = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)

    alpha = 1.0 / period
    avg_gains = np.zeros_like(gains, dtype=np.float64)
    avg_losses = np.zeros_like(losses, dtype=np.float64)

    avg_gains[0] = gains[0]
    avg_losses[0] = losses[0]

    for i in range(1, len(gains)):
        avg_gains[i] = alpha * gains[i] + (1 - alpha) * avg_gains[i-1]
        avg_losses[i] = alpha * losses[i] + (1 - alpha) * avg_losses[i-1]

    with np.errstate(divide='ignore', invalid='ignore'):
        rs = avg_gains / avg_losses

    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = np.nan_to_num(rsi, nan=50.0, posinf=100.0, neginf=0.0)

    return rsi
