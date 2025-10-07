import pandas as pd
from ....stock_address import StockAddress
from .strategy.base import BaseSaveStrategy
from simple_logger import init_logging, func_logging


class SaveWorker:
    """데이터 저장 작업 흐름 관장"""

    @init_logging
    def __init__(self, strategy: BaseSaveStrategy):
        """
        Args:
            strategy: BaseSaveStrategy 인스턴스
        """
        self.strategy = strategy

    @func_logging
    def __call__(self, address: StockAddress, df: pd.DataFrame, storage_last_ts: int = None) -> None:
        """
        데이터 저장 실행

        Args:
            address: StockAddress 객체
            df: 저장할 DataFrame
            storage_last_ts: 저장소에 기록된 마지막 타임스탬프
        """
        # 저장 전 timestamp 검증 (방어적 프로그래밍)
        self._validate_timestamp(df)

        self.strategy.save(address, df, storage_last_ts)

    @staticmethod
    def _validate_timestamp(df: pd.DataFrame) -> None:
        """
        timestamp가 초 단위인지 검증

        Args:
            df: 검증할 DataFrame

        Raises:
            ValueError: 밀리초 timestamp 감지 시
        """
        if df is None or df.empty:
            return

        if 'timestamp' not in df.columns:
            return

        # 밀리초 판단 기준: 10^10 (2286-11-20 17:46:40 UTC)
        TIMESTAMP_SECOND_MAX = 10_000_000_000

        max_ts = df['timestamp'].max()

        if max_ts >= TIMESTAMP_SECOND_MAX:
            raise ValueError(
                f"Millisecond timestamps detected in DataFrame (max: {max_ts}). "
                f"This should have been normalized by Candle class. "
                f"Please report this as a bug."
            )
