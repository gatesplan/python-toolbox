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
        self.strategy.save(address, df, storage_last_ts)
